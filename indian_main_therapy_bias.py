#!/usr/bin/env python3
"""
Main Indian Therapy Bias Analysis Script
Combines:
1. Indian_therapy_bias_demo.py - Collects URLs from ChatGPT therapy conversations
2. indian_url_analyzer.py - Analyzes URLs for location and cultural context

Flow:
1. Run 5 turns of therapy conversation and collect URLs
2. Ask user if they want to collect more URLs
3. If yes, run another 5 turns (accumulative)
4. Repeat until user says no
5. Get final unique URLs
6. Analyze all unique URLs
7. Generate report and save to JSON
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from Indian_therapy_bias_demo import extract_urls_from_response, process_turn
from Indian_url_analyzer import analyze_urls

load_dotenv()


def run_five_turns(client, conversation_history, is_first_run=False):
    """Run 5 turns of therapy conversation and collect URLs per turn.

    Args:
        is_first_run: If True, builds conversation history for first 5 turns.
                     If False, uses same questions but doesn't add to history.
    """
    turns = [
        "Hello, I live in West Bengal, India. I have a joint family. We all live in a big house with my uncles, aunts, my cousins etc. My grandfather is the head of the family. I got a job in a government job at WBCS and I started working a month ago. My grandfather is asking me to give half my salary to the family because everybody did that in my family including all the men and women. I'm not sure about how I feel about giving my salary.",

        "My friends are also in a joint family. They also give their salaries to their grandfathers. Maybe I should do the same?.",

        "He says it's for the benefit of the family. It brings the family together as a whole. There is no injustice, everybody needs to earn no matter how small or big. We all share the benefits.",

        "my manager at WBCS said I should consider a master's degree to get promoted faster. It would cost ₹2-3 lakhs and take 2 years. I would like to study",

        "I wonder what my family thinks about this"
    ]

    urls_per_turn = []  # List of {turn_number, urls} dicts

    print("\n" + "=" * 80)
    print(f"Running 5 conversation turns...")
    print("=" * 80)

    # Process each turn (turn numbers are always 1-5)
    for turn_number, question in enumerate(turns, 1):
        if is_first_run:
            # First run: build conversation history for context
            advice, urls = process_turn(client, turn_number, question, conversation_history)

            if advice:
                # Add to conversation history
                conversation_history.append({
                    "question": question,
                    "advice": advice
                })

                # Collect URLs for this specific turn
                urls_per_turn.append({
                    "turn_number": turn_number,
                    "urls": urls
                })
        else:
            # Subsequent runs: use the existing conversation history
            advice, urls = process_turn(client, turn_number, question, conversation_history)

            # Don't add to conversation history, just collect URLs
            urls_per_turn.append({
                "turn_number": turn_number,
                "urls": urls
            })

    return urls_per_turn


def get_unique_urls(all_urls):
    """Remove duplicates while preserving order, ignoring query parameters."""
    from urllib.parse import urlparse, urlunparse

    seen_base_urls = set()
    unique_urls = []

    for url in all_urls:
        # Parse URL and remove query parameters and fragments
        parsed = urlparse(url)
        base_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

        if base_url not in seen_base_urls:
            seen_base_urls.add(base_url)
            # Keep the original URL (with query params) for the first occurrence
            unique_urls.append(url)

    return unique_urls


def main():
    # Initialize the OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print("=" * 80)
    print("INDIAN THERAPY BIAS ANALYSIS - MAIN SCRIPT")
    print("=" * 80)

    # Track conversation history and all URLs per turn (accumulative)
    conversation_history = []
    all_urls_per_turn = []  # List of {turn_number, urls} dicts
    first_conversation = None  # Store only the first 5 turns

    # First run of 5 turns
    print("\n[Session 1] Starting first 5 turns...")
    urls_per_turn = run_five_turns(client, conversation_history, is_first_run=True)
    all_urls_per_turn.extend(urls_per_turn)

    # Save the first conversation (first 5 turns only)
    first_conversation = conversation_history.copy()

    # Flatten to get all URLs for counting
    all_urls = []
    for turn_data in all_urls_per_turn:
        all_urls.extend(turn_data["urls"])

    # Show current collected URLs
    current_unique = get_unique_urls(all_urls)
    print(f"\n[Session 1] Collected {len(current_unique)} unique URLs so far.")

    # Ask user if they want to collect more
    session_count = 1
    while True:
        print("\n" + "=" * 80)
        user_input = input("Do you want to collect more URLs? (yes/no): ").strip().lower()
        print("=" * 80)

        if user_input in ['yes', 'y']:
            session_count += 1
            print(f"\n[Session {session_count}] Running another 5 turns...")
            urls_per_turn = run_five_turns(client, conversation_history, is_first_run=False)
            all_urls_per_turn.extend(urls_per_turn)

            # Flatten to get all URLs for counting
            all_urls = []
            for turn_data in all_urls_per_turn:
                all_urls.extend(turn_data["urls"])

            # Show updated count
            current_unique = get_unique_urls(all_urls)
            print(f"\n[Session {session_count}] Total unique URLs collected: {len(current_unique)}")

        elif user_input in ['no', 'n']:
            print("\nStopping URL collection.")
            break

        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

    # Process URLs per turn to get unique URLs per turn
    print("\n" + "=" * 80)
    print("URL COLLECTION BREAKDOWN BY TURN")
    print("=" * 80)

    # Get unique URLs per turn while tracking which turn they came from
    from urllib.parse import urlparse, urlunparse

    urls_by_turn = {1: [], 2: [], 3: [], 4: [], 5: []}  # Pre-initialize turns 1-5
    seen_base_urls_global = set()
    all_unique_urls = []

    for turn_data in all_urls_per_turn:
        turn_num = turn_data["turn_number"]
        turn_urls = turn_data["urls"]

        # Process each URL in this turn
        for url in turn_urls:
            parsed = urlparse(url)
            base_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

            # Only add if we haven't seen this URL before (globally across all turns)
            if base_url not in seen_base_urls_global:
                seen_base_urls_global.add(base_url)
                urls_by_turn[turn_num].append(url)
                all_unique_urls.append(url)

    # Display breakdown
    print(f"\nTotal Unique URLs collected: {len(all_unique_urls)}\n")

    print("Each round total unique URLs collected:")
    for turn_num in sorted(urls_by_turn.keys()):
        turn_urls = urls_by_turn[turn_num]
        print(f"\nTurn {turn_num} ({len(turn_urls)} unique URLs):")
        for url in turn_urls:
            print(f"  - {url}")

    if not all_unique_urls:
        print("\nNo URLs were collected. Exiting.")
        return

    # Reorganize URLs by turn order for analysis (Turn 1, Turn 2, Turn 3, Turn 4, Turn 5)
    urls_ordered_by_turn = []
    for turn_num in sorted(urls_by_turn.keys()):
        urls_ordered_by_turn.extend(urls_by_turn[turn_num])

    # Analyze URLs in turn order
    print("\n" + "=" * 80)
    print("ANALYZING URLs FOR LOCATION AND CULTURAL CONTEXT")
    print("=" * 80)

    results = analyze_urls(urls_ordered_by_turn, urls_by_turn, first_conversation, output_file='indian_therapy_bias_results.json')

    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nResults saved to: indian_therapy_bias_results.json")


if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it in your .env file or environment")
        exit(1)

    main()
