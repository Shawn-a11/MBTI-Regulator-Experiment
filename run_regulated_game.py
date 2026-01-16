# Copyright (c) 2025 ETH Zurich.
#                    All rights reserved.
#
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# Run games with regulator agent

import sys
import os

# Independent project - use local dependencies
current_dir = os.path.dirname(os.path.abspath(__file__))
dependencies_dir = os.path.join(current_dir, 'dependencies')
sys.path.insert(0, dependencies_dir)

import pandas as pd
from games_structures.base_game import BaseGameStructure, GameState
from langchain_community.callbacks.openai_info import OpenAICallbackHandler
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, Send
from typing import Literal, Callable, TypedDict, Annotated, List
from operator import add

# Import from local modules
from models import get_model_by_id_and_provider
from regulator_agent import RegulatorAgent
from game_variant_generator import GameVariantGenerator

# Import node helpers from local dependencies
import json
from langchain_core.messages import SystemMessage

# Import node_helpers module FIRST
import node_helpers as nh_module

# Fix personality file path BEFORE importing functions that use it
# Use local dependencies directory
_priming_path = os.path.join(current_dir, 'dependencies', 'priming', 'priming_without_mention_of_mbti_different_none_with_altruistic_selfish.json')

# Monkey patch get_personality_from_key_prompt BEFORE importing it
def _get_personality_from_key_prompt_fixed(personality_key: str) -> SystemMessage:
    """Get personality prompt with correct path resolution."""
    if not os.path.exists(_priming_path):
        raise FileNotFoundError(
            f"Personality file not found at: {_priming_path}\n"
            f"Current working directory: {os.getcwd()}\n"
            f"Script directory: {current_dir}\n"
            f"Please ensure dependencies are properly set up."
        )
    personalities = json.load(open(_priming_path))
    if personality_key not in personalities:
        available = list(personalities.keys())[:10]
        raise KeyError(
            f"Personality '{personality_key}' not found in personality file.\n"
            f"Available personalities: {available}..."
        )
    return SystemMessage(personalities[personality_key])

# Patch the function in the imported module BEFORE importing functions that use it
nh_module.get_personality_from_key_prompt = _get_personality_from_key_prompt_fixed

# Now import functions (they will use the patched version)
from node_helpers import (
    load_game_structure_from_registry,
    get_answer_format,
    get_question_prompt,
    get_agent_annotated_prompt,
    AnnotatedPrompt
)


class RegulatedGameState(GameState):
    """
    Extended game state that includes regulator information.
    """
    variant_description: str
    variant_complexity: str
    variant_reasoning: str
    regulator_model: str


def send_prompts_node(prompt_type : Literal["message", "action"], GameStructure: BaseGameStructure) -> Callable:
    """
    Get the function to send the prompts to the agents.
    For 3 RPM limit, we need to send sequentially, not in parallel.
    """
    def send_prompts(state: RegulatedGameState) -> list[Send]:
        # Return only agent_1 first to ensure sequential execution
        agent_1_annotated_prompt_state = get_agent_annotated_prompt("agent_1", state, prompt_type, GameStructure)
        # 为 message 和 action 都使用带编号的节点名
        return [Send(f"invoke_from_prompt_state_{prompt_type}_1", agent_1_annotated_prompt_state)]
    return send_prompts

def send_second_agent_prompt_node(prompt_type : Literal["message", "action"], GameStructure: BaseGameStructure) -> Callable:
    """
    Send prompt to the second agent after the first one completes.
    """
    def send_second_prompt(state: RegulatedGameState) -> list[Send]:
        agent_2_annotated_prompt_state = get_agent_annotated_prompt("agent_2", state, prompt_type, GameStructure)
        # 为 message 和 action 都使用带编号的节点名
        return [Send(f"invoke_from_prompt_state_{prompt_type}_2", agent_2_annotated_prompt_state)]
    return send_second_prompt


def invoke_from_prompt_state_node(models, GameStructure) -> Callable:
    """
    Get the function to invoke the model from the prompt state.
    """
    import time
    from openai import RateLimitError, APIConnectionError
    try:
        from httpx import RemoteProtocolError
    except ImportError:
        RemoteProtocolError = Exception
    
    def invoke_from_prompt_state(state : AnnotatedPrompt) -> Command:
        json_mode = False
        try:
            for model in models.values():
                if hasattr(model, 'model_name') and model.model_name == "deepseek-chat":
                    json_mode = True
        except:
            pass

        prompt = state.prompt
        agent_name = state.agent_name
        prompt_type = state.prompt_type
        model = models[agent_name]
        Structure = GameStructure.MessageResponse if prompt_type == "message" else GameStructure.ActionResponse
        
        # 移除延迟，直接调用API进行测试
        # time.sleep(30)  # 已移除长时间等待
        
        # Retry logic for rate limit errors
        max_retries = 5
        retry_delay = 2  # 减少重试延迟，快速测试
        
        for attempt in range(max_retries):
            try:
                if json_mode:
                    response = model.with_structured_output(Structure, method="json_mode", include_raw=True).invoke(prompt)
                    message = ""
                    if prompt_type == "message":
                        message = response["parsed"].message
                    else:
                        message = response["parsed"].action
                else:
                    # Use json_schema method for better OpenRouter compatibility
                    # OpenRouter has region restrictions with function_calling, so always use json_schema
                    response = model.with_structured_output(Structure, method="json_schema").invoke(prompt)
                    message = response.message if prompt_type == "message" else response.action
                print(f"Agent {agent_name} {prompt_type} : {message}")
                return Command(update = {f"{agent_name}_{prompt_type}s": [message]})
            except Exception as e:
                # Handle different types of errors
                error_str = str(e).lower()
                error_type = type(e).__name__
                
                # Check for rate limit errors
                is_rate_limit = ("rate limit" in error_str or "429" in error_str or 
                               isinstance(e, RateLimitError) or "too many requests" in error_str)
                
                # Check for connection errors (network issues, server disconnects)
                is_connection_error = (isinstance(e, (APIConnectionError, RemoteProtocolError)) or
                                     "connection" in error_str or "disconnected" in error_str or
                                     "server disconnected" in error_str or "timeout" in error_str)
                
                if (is_rate_limit or is_connection_error) and attempt < max_retries - 1:
                    error_msg = str(e)
                    
                    # For rate limits, try to extract wait time
                    if is_rate_limit and "try again in" in error_msg.lower():
                        import re
                        wait_match = re.search(r'(\d+)s', error_msg)
                        if wait_match:
                            retry_delay = int(wait_match.group(1)) + 2
                    elif is_connection_error:
                        # For connection errors, use exponential backoff
                        retry_delay = min(20 * (2 ** attempt), 60)  # Max 60 seconds
                        print(f"Connection error ({error_type}). Retrying with exponential backoff...")
                    
                    if is_rate_limit:
                        print(f"Rate limit reached (OpenRouter/OpenAI). Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...")
                    else:
                        print(f"Connection error ({error_type}). Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...")
                    
                    time.sleep(retry_delay)
                else:
                    # For other errors or max retries reached, raise immediately
                    print(f"Error after {attempt + 1} attempts: {error_type}: {str(e)}")
                    raise
            except Exception as e:
                # For other errors, raise immediately
                raise
    return invoke_from_prompt_state


def judge_intent_node(model, GameStructure) -> Callable:
    """
    Get the function to judge the intent of the agents.
    """
    import time
    from openai import RateLimitError, APIConnectionError
    try:
        from httpx import RemoteProtocolError
    except ImportError:
        RemoteProtocolError = Exception
    
    def judge_intent(state: RegulatedGameState) -> Command:
        # Check if all required data is available with detailed error message
        agent_1_messages = state.get("agent_1_messages", [])
        agent_2_messages = state.get("agent_2_messages", [])
        agent_1_actions = state.get("agent_1_actions", [])
        agent_2_actions = state.get("agent_2_actions", [])
        
        if len(agent_1_messages) == 0:
            print(f"Error: agent_1_messages is empty. State keys: {list(state.keys())}")
            return Command(update={})
        if len(agent_2_messages) == 0:
            print(f"Error: agent_2_messages is empty. State keys: {list(state.keys())}")
            return Command(update={})
        if len(agent_1_actions) == 0:
            print(f"Error: agent_1_actions is empty.")
            print(f"  agent_1_messages length: {len(agent_1_messages)}")
            print(f"  agent_2_messages length: {len(agent_2_messages)}")
            print(f"  agent_2_actions length: {len(agent_2_actions)}")
            return Command(update={})
        if len(agent_2_actions) == 0:
            print(f"Error: agent_2_actions is empty.")
            print(f"  agent_1_messages length: {len(agent_1_messages)}")
            print(f"  agent_2_messages length: {len(agent_2_messages)}")
            print(f"  agent_1_actions length: {len(agent_1_actions)}")
            return Command(update={})
        
        message_1 = agent_1_messages[-1]
        message_2 = agent_2_messages[-1]
        action_1 = agent_1_actions[-1]
        action_2 = agent_2_actions[-1]
        
        question = get_question_prompt(GameStructure)
        answer_format = get_answer_format(GameStructure)
        
        # 移除延迟，直接调用API进行测试
        # time.sleep(30)  # 已移除长时间等待
        
        # Retry logic for rate limit errors
        max_retries = 5
        retry_delay = 2  # 减少重试延迟，快速测试
        
        for attempt in range(max_retries):
            try:
                response_1 = model.with_structured_output(answer_format).invoke(
                    f"{question} : {message_1}"
                )
                # 移除延迟，直接调用API进行测试
                # time.sleep(30)  # 已移除长时间等待
                response_2 = model.with_structured_output(answer_format).invoke(
                    f"{question} : {message_2}"
                )
                
                intent_agent_1 = response_1.answer
                intent_agent_2 = response_2.answer
                truthful_agent_1 = intent_agent_1 == action_1
                truthful_agent_2 = intent_agent_2 == action_2
                analysis_agent_1 = response_1.analysis
                analysis_agent_2 = response_2.analysis
                return Command(update = {
                    "intent_agent_1": [intent_agent_1],
                    "intent_agent_2": [intent_agent_2],
                    "truthful_agent_1": [truthful_agent_1],
                    "truthful_agent_2": [truthful_agent_2],
                    "analysis_agent_1": [analysis_agent_1],
                    "analysis_agent_2": [analysis_agent_2]
                })
            except Exception as e:
                # Handle different types of errors
                error_str = str(e).lower()
                error_type = type(e).__name__
                
                # Check for rate limit errors
                is_rate_limit = ("rate limit" in error_str or "429" in error_str or 
                               isinstance(e, RateLimitError) or "too many requests" in error_str)
                
                # Check for connection errors (network issues, server disconnects)
                is_connection_error = (isinstance(e, (APIConnectionError, RemoteProtocolError)) or
                                     "connection" in error_str or "disconnected" in error_str or
                                     "server disconnected" in error_str or "timeout" in error_str)
                
                if (is_rate_limit or is_connection_error) and attempt < max_retries - 1:
                    error_msg = str(e)
                    
                    # For rate limits, try to extract wait time
                    if is_rate_limit and "try again in" in error_msg.lower():
                        import re
                        wait_match = re.search(r'(\d+)s', error_msg)
                        if wait_match:
                            retry_delay = int(wait_match.group(1)) + 2
                    elif is_connection_error:
                        # For connection errors, use exponential backoff
                        retry_delay = min(10 * (2 ** attempt), 60)  # Max 60 seconds
                    
                    if is_rate_limit:
                        print(f"Rate limit reached in intent analysis. Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...")
                    else:
                        print(f"Connection error in intent analysis ({error_type}). Waiting {retry_delay} seconds before retry {attempt + 1}/{max_retries}...")
                    
                    time.sleep(retry_delay)
                else:
                    print(f"Error in intent analysis after {attempt + 1} attempts: {error_type}: {str(e)}")
                    raise
    return judge_intent


def update_state_node(GameStructure):
    """
    Get the function to update the state of the game.
    """
    def update_state(state: RegulatedGameState):
        # 使用Command返回状态更新，并在应该结束时直接跳转到END
        agent_1_decision = state["agent_1_actions"][-1]
        agent_2_decision = state["agent_2_actions"][-1]
        score_agent1, score_agent2 = GameStructure.payoff_matrix[(agent_1_decision, agent_2_decision)]
        
        # 增加轮次
        new_round = state["current_round"] + 1
        
        print(f"📊 Round {state['current_round']} completed: Agent 1={agent_1_decision}, Agent 2={agent_2_decision}, Scores: ({score_agent1}, {score_agent2})", flush=True)
        print(f"   更新后轮次: {new_round}/{state['total_rounds']}", flush=True)
        
        state_updates = {
            "agent_1_scores": [score_agent1],
            "agent_2_scores": [score_agent2],
            "current_round": new_round
        }
        
        # 返回状态更新，让conditional_edges检查是否继续
        # 注意：不要使用goto=END，因为这会阻止状态更新被应用
        return Command(update=state_updates)
    return update_state


def should_continue(state: RegulatedGameState) -> bool:
    # update_state已经将current_round增加了1
    # 所以如果current_round > total_rounds，说明已经完成了所有轮次
    current = state.get("current_round", 1)
    total = state.get("total_rounds", 1)
    should = current <= total
    
    if not should:
        completed_rounds = current - 1
        print(f"✅ 游戏结束: 已完成 {completed_rounds}/{total} 轮 (current_round={current})", flush=True)
        return False
    else:
        print(f"🔄 继续游戏: 当前轮次 {current}/{total}", flush=True)
        return True


def run_regulated_game(
    regulator_model_id: str,
    regulator_provider: str,
    player_model_1: str,
    player_provider_1: str,
    player_model_2: str,
    player_provider_2: str,
    total_rounds: int,
    personality_key_1: str,
    personality_key_2: str,
    base_game_name: str,
    variant_type: str = "complex",
    file_path: str = None
) -> RegulatedGameState:
    """
    Run a game with a regulator agent generating variants.
    
    Args:
        regulator_model_id (str): Model ID for regulator (e.g., "gpt-4o")
        regulator_provider (str): Provider for regulator model
        player_model_1 (str): Model ID for player 1 (e.g., "gpt-4o-mini")
        player_provider_1 (str): Provider for player 1 model
        player_model_2 (str): Model ID for player 2
        player_provider_2 (str): Provider for player 2 model
        total_rounds (int): Number of rounds to play
        personality_key_1 (str): MBTI personality for player 1
        personality_key_2 (str): MBTI personality for player 2
        base_game_name (str): Name of the base game
        variant_type (str): Type of variant to generate
        file_path (str): Path to save results
    
    Returns:
        RegulatedGameState: Final game state
    """
    # Step 1: Load base game
    base_game = load_game_structure_from_registry(base_game_name)
    
    # Step 2: Generate variant using regulator agent
    # IMPORTANT: Create regulator BEFORE creating player models
    # This ensures environment variables are correctly set for OpenRouter
    import sys
    sys.stdout.flush()
    print(f"📝 Generating game variant using regulator agent ({regulator_model_id})...", flush=True)
    
    # Create regulator FIRST (before any player models)
    # This ensures OpenAI keys are removed during model creation
    regulator = RegulatorAgent(regulator_model_id, regulator_provider)
    variant_response = regulator.generate_game_variant(base_game, variant_type)
    
    print(f"Variant generated - Complexity: {variant_response.complexity_level}")
    print(f"Reasoning: {variant_response.reasoning[:200]}...")
    
    # Step 3: Create variant game structure
    variant_game = GameVariantGenerator.create_variant_game(base_game, variant_response)
    
    # Step 4: Validate variant
    is_valid, error_msg = GameVariantGenerator.validate_variant(base_game, variant_response)
    if not is_valid:
        print(f"Warning: Variant validation failed: {error_msg}")
        print("Falling back to base game...")
        variant_game = base_game
    else:
        # Additional check: verify payoff matrix has correct keys
        payoff = variant_game.payoff_matrix
        base_payoff = base_game.payoff_matrix
        missing_keys = set(base_payoff.keys()) - set(payoff.keys())
        if missing_keys:
            print(f"Warning: Variant payoff matrix missing keys: {missing_keys}")
            print("Falling back to base game...")
            variant_game = base_game
        else:
            print(f"✓ Variant payoff matrix validated: {len(payoff)} action combinations")
    
    # Step 5: Set up player models
    models = {
        "agent_1": get_model_by_id_and_provider(player_model_1, provider=player_provider_1),
        "agent_2": get_model_by_id_and_provider(player_model_2, provider=player_provider_2)
    }
    
    intent_model = get_model_by_id_and_provider("gpt-4o-mini")
    callback_handler = OpenAICallbackHandler()
    
    # Step 6: Create graph with sequential execution for rate limit compliance
    graph = StateGraph(RegulatedGameState, input = RegulatedGameState, output = RegulatedGameState)
    
    # Lambda nodes for sequential state management
    graph.add_node("lambda_to_messages", lambda x: {})
    graph.add_node("lambda_from_messages_1", lambda x: {})  # After agent_1 message
    graph.add_node("lambda_from_messages_2", lambda x: {})  # After agent_2 message
    graph.add_node("lambda_from_actions_1", lambda x: {})   # After agent_1 action
    graph.add_node("lambda_from_actions_2", lambda x: {})   # After agent_2 action
    
    # Invoke nodes - separate nodes for each agent to avoid state conflicts
    # Message nodes: separate for agent_1 and agent_2
    graph.add_node(f"invoke_from_prompt_state_message_1", invoke_from_prompt_state_node(models, variant_game))
    graph.add_node(f"invoke_from_prompt_state_message_2", invoke_from_prompt_state_node(models, variant_game))
    # Action nodes: separate for agent_1 and agent_2
    graph.add_node(f"invoke_from_prompt_state_action_1", invoke_from_prompt_state_node(models, variant_game))
    graph.add_node(f"invoke_from_prompt_state_action_2", invoke_from_prompt_state_node(models, variant_game))
    graph.add_node("judge_intent", judge_intent_node(intent_model, variant_game))
    graph.add_node("update_state", update_state_node(variant_game))
    
    # Message phase: Sequential execution (agent_1 -> agent_2)
    graph.add_edge(START, "lambda_to_messages")
    # Agent 1 message
    graph.add_conditional_edges(
        source = "lambda_to_messages", 
        path = send_prompts_node("message", variant_game),
        path_map = ["invoke_from_prompt_state_message_1"]
    )
    graph.add_edge("invoke_from_prompt_state_message_1", "lambda_from_messages_1")
    # Agent 2 message (after agent 1 completes) - use separate node
    graph.add_conditional_edges(
        source = "lambda_from_messages_1",
        path = send_second_agent_prompt_node("message", variant_game),
        path_map = ["invoke_from_prompt_state_message_2"]
    )
    graph.add_edge("invoke_from_prompt_state_message_2", "lambda_from_messages_2")
    
    # Action phase: Sequential execution (agent_1 -> agent_2)
    graph.add_conditional_edges(
        source = "lambda_from_messages_2", 
        path = send_prompts_node("action", variant_game),
        path_map = ["invoke_from_prompt_state_action_1"]
    )
    graph.add_edge("invoke_from_prompt_state_action_1", "lambda_from_actions_1")
    # Agent 2 action (after agent 1 completes) - use separate node
    graph.add_conditional_edges(
        source = "lambda_from_actions_1",
        path = send_second_agent_prompt_node("action", variant_game),
        path_map = ["invoke_from_prompt_state_action_2"]
    )
    graph.add_edge("invoke_from_prompt_state_action_2", "lambda_from_actions_2")
    
    # Intent analysis and state update
    graph.add_edge("lambda_from_actions_2", "judge_intent")
    graph.add_edge("judge_intent", "update_state")
    
    # update_state现在会返回Command(goto=END)或Command(update=...)
    # 如果返回goto=END，LangGraph会直接跳转到END，不会执行conditional_edges
    # 如果返回update=...，conditional_edges会检查should_continue
    graph.add_conditional_edges(
        source = "update_state",
        path = should_continue,
        path_map = {
            False : END,
            True : "lambda_to_messages"
        }
    )
    
    # Step 7: Compile and run
    compiled_graph = graph.compile()
    
    # Create initial state with empty lists initialized
    initial_state = RegulatedGameState(
        personality_key_1=personality_key_1,
        personality_key_2=personality_key_2,
        current_round=1,
        total_rounds=total_rounds,
        variant_description=variant_response.variant_description,
        variant_complexity=variant_response.complexity_level,
        variant_reasoning=variant_response.reasoning,
        regulator_model=regulator_model_id,
        # Initialize empty lists to avoid IndexError
        agent_1_messages=[],
        agent_2_messages=[],
        agent_1_actions=[],
        agent_2_actions=[],
        agent_1_scores=[],
        agent_2_scores=[],
        intent_agent_1=[],
        intent_agent_2=[],
        truthful_agent_1=[],
        truthful_agent_2=[],
        analysis_agent_1=[],
        analysis_agent_2=[]
    )
    
    end_state = compiled_graph.invoke(initial_state, config={"recursion_limit": 200, "callbacks": [callback_handler]})
    print(f"Total Cost (USD): ${callback_handler.total_cost}")
    
    # Step 8: Save results
    if file_path:
        columns = [
            "game_name", "base_game_name", "variant_type", "regulator_model",
            "model_provider_1", "model_name_1", "model_provider_2", "model_name_2",
            "personality_1", "personality_2", "variant_complexity",
            "agent_1_scores", "agent_2_scores", "agent_1_messages", "agent_2_messages",
            "agent_1_actions", "agent_2_actions", "intent_agent_1", "intent_agent_2",
            "truthful_agent_1", "truthful_agent_2", "analysis_agent_1", "analysis_agent_2",
            "total_rounds", "total_tokens", "total_cost_USD", "variant_reasoning"
        ]

        end_state["agent_1_messages"] = [msg.replace('"', "'") for msg in end_state["agent_1_messages"]]
        end_state["agent_2_messages"] = [msg.replace('"', "'") for msg in end_state["agent_2_messages"]]
        end_state["agent_1_actions"] = [action.replace('"', "'") for action in end_state["agent_1_actions"]]
        end_state["agent_2_actions"] = [action.replace('"', "'") for action in end_state["agent_2_actions"]]

        new_row = pd.DataFrame([{
            "game_name": variant_game.game_name,
            "base_game_name": base_game_name,
            "variant_type": variant_type,
            "regulator_model": regulator_model_id,
            "model_provider_1": player_provider_1,
            "model_name_1": player_model_1,
            "model_provider_2": player_provider_2,
            "model_name_2": player_model_2,
            "personality_1": personality_key_1,
            "personality_2": personality_key_2,
            "variant_complexity": variant_response.complexity_level,
            "agent_1_scores": end_state["agent_1_scores"],
            "agent_2_scores": end_state["agent_2_scores"],
            "agent_1_messages": end_state["agent_1_messages"],
            "agent_2_messages": end_state["agent_2_messages"],
            "agent_1_actions": end_state["agent_1_actions"],
            "agent_2_actions": end_state["agent_2_actions"],
            "intent_agent_1": end_state["intent_agent_1"],
            "intent_agent_2": end_state["intent_agent_2"],
            "truthful_agent_1": end_state["truthful_agent_1"],
            "truthful_agent_2": end_state["truthful_agent_2"],
            "analysis_agent_1": end_state["analysis_agent_1"],
            "analysis_agent_2": end_state["analysis_agent_2"],
            "total_rounds": total_rounds,
            "total_tokens": callback_handler.total_tokens,
            "total_cost_USD": callback_handler.total_cost,
            "variant_reasoning": variant_response.reasoning[:500]  # Truncate for CSV
        }])
        
        try:
            df = pd.read_csv(file_path)
        except FileNotFoundError:
            df = new_row
        else:
            df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(file_path, mode='w', header=True, index=False)
        print(f"Results saved to {file_path}")
    
    return end_state
