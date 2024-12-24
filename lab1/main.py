from typing import Dict, List
from autogen import ConversableAgent
import sys
import os
import math
import re


def fetch_restaurant_data(restaurant_name: str) -> Dict[str, List[str]]:
    # TODO
    # This function takes in a restaurant name and returns the reviews for that restaurant. 
    # The output should be a dictionary with the key being the restaurant name and the value being a list of reviews for that restaurant.
    # The "data fetch agent" should have access to this function signature, and it should be able to suggest this as a function call. 
    # Example:
    # > fetch_restaurant_data("Applebee's")
    # {"Applebee's": ["The food at Applebee's was average, with nothing particularly standing out.", ...]}
    with open('restaurant-data.txt', 'r') as f:
      reviews = f.readlines()
    
    # Filter reviews for the requested restaurant
    restaurant_reviews = [
      review.strip()
      for review in reviews
      if review.lower().startswith(restaurant_name.lower() + ".")
    ]
    
    return { restaurant_name: restaurant_reviews}


def calculate_overall_score(restaurant_name: str, food_scores: List[int], customer_service_scores: List[int]) -> Dict[str, float]:
    # TODO
    # This function takes in a restaurant name, a list of food scores from 1-5, and a list of customer service scores from 1-5
    # The output should be a score between 0 and 10, which is computed as the following:
    # SUM(sqrt(food_scores[i]**2 * customer_service_scores[i]) * 1/(N * sqrt(125)) * 10
    # The above formula is a geometric mean of the scores, which penalizes food quality more than customer service. 
    # Example:
    # > calculate_overall_score("Applebee's", [1, 2, 3, 4, 5], [1, 2, 3, 4, 5])
    # {"Applebee's": 5.048}
    # NOTE: be sure to that the score includes AT LEAST 3  decimal places. The public tests will only read scores that have 
    # at least 3 decimal places.
    N = len(food_scores)
    if N == 0:
      return { restaurant_name: 0.000}
    
    score = sum(math.sqrt(food_scores[i]**2 * customer_service_scores[i]) * 1/(N * math.sqrt(125)) * 10 
            for i in range(N))
    
    return { restaurant_name: round(score, 3)}


def get_data_fetch_agent_prompt() -> str:
    # TODO
    # It may help to organize messages/prompts within a function which returns a string. 
    # For example, you could use this function to return a prompt for the data fetch agent 
    # to use to fetch reviews for a specific restaurant.
    return f"""Extract the restaurant name from the query:
Call fetch_restaurant_data with the restaurant name as the argument.
The function will return a dictionary with restaurant reviews."""

# TODO: feel free to write as many additional functions as you'd like.
def get_review_analyzer_prompt() -> str:
  return """Analyze each review and extract food and service scores using these keywords:
Score 1: awful, horrible, disgusting
Score 2: bad, unpleasant, offensive
Score 3: average, uninspiring, forgettable
Score 4: good, enjoyable, satisfying
Score 5: awesome, incredible, amazing

For each review:
1. Find keyword for food quality -> assign food_score
2. Find keyword for service quality -> assign customer_service_score

List all scores in format:
Review 1: food_score=X, customer_service_score=Y
Review 2: food_score=X, customer_service_score=Y
etc."""

def get_scoring_agent_prompt() -> str:
    return """Based on the food and customer service scores from all reviews:
1. Extract all food_scores into a list
2. Extract all customer_service_scores into a list
3. Call calculate_overall_score with:
   - restaurant name
   - food_scores list
   - customer_service_scores list"""

# Do not modify the signature of the "main" function.
def main(user_query: str):
    entrypoint_agent_system_message = """You are the supervisor agent coordinating restaurant review analysis.
Your tasks:
1. Work with data fetch agent to get restaurant reviews
2. Pass reviews to analyzer agent for scoring
3. Send scores to scoring agent for final calculation"""

    # example LLM config for the entrypoint agent
    llm_config = {"config_list": [{"model": "gpt-4o-mini", "api_key": ''}]}
    # the main entrypoint/supervisor agent
    entrypoint_agent = ConversableAgent("entrypoint_agent", 
                                        system_message=entrypoint_agent_system_message, 
                                        llm_config=llm_config)
    entrypoint_agent.register_for_llm(name="fetch_restaurant_data", description="Fetches the reviews for a specific restaurant.")(fetch_restaurant_data)
    entrypoint_agent.register_for_execution(name="fetch_restaurant_data")(fetch_restaurant_data)
    
    # TODO
    # Create more agents here. 
    data_fetch_agent = ConversableAgent(
        "data_fetch_agent",
        system_message="You help fetch restaurant review data by suggesting the appropriate function call.",
        llm_config=llm_config
    )

    review_analyzer = ConversableAgent(
        "review_analyzer", 
        system_message="""You analyze restaurant reviews and extract food and service scores based on keywords...""",
        llm_config=llm_config
    )

    scoring_agent = ConversableAgent(
        "scoring_agent",
        system_message="You calculate final restaurant scores based on food and service scores.",
        llm_config=llm_config
    )

    data_fetch_agent.register_function(
        function_map={
            "fetch_restaurant_data": fetch_restaurant_data,
            "calculate_overall_score": calculate_overall_score
        }
    )

    review_analyzer.register_function(
        function_map={
            "calculate_overall_score": calculate_overall_score
        }
    )

    scoring_agent.register_function(
        function_map={
            "calculate_overall_score": calculate_overall_score
        }
    )

    # Initiate sequential chats
    result = entrypoint_agent.initiate_chats([
        {
            "recipient": data_fetch_agent,
            "message": get_data_fetch_agent_prompt(),
            "summary_method": "last_msg",
            "max_messages": 3
        },
        {
            "recipient": review_analyzer, 
            "message": get_review_analyzer_prompt(),
            "summary_method": "last_msg",
            "max_messages": 3
        },
        {
            "recipient": scoring_agent,
            "message": get_scoring_agent_prompt(),
            "summary_method": "last_msg",
            "max_messages": 3
        }
    ])

    return result
    
# DO NOT modify this code below.
if __name__ == "__main__":
    assert len(sys.argv) > 1, "Please ensure you include a query for some restaurant when executing main."
    main(sys.argv[1])