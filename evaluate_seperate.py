"""
Evaluate the agent on individual train files (train_1.json through train_10.json).
This script allows you to test each question separately.
Make sure to set the API key in the `my_agent/.env` file. See `README.md` for more details.
"""

import argparse
import datetime
import json
import os
import pathlib
import time

import dotenv
import pydantic
from google import genai
from colorama import Fore, Style, init

from utils import server

# Initialize colorama for cross-platform color support
init(autoreset=True)

dotenv.load_dotenv(dotenv_path=pathlib.Path("my_agent/.env"))


class JudgeResponse(pydantic.BaseModel):
    """Pydantic model for LLM judge response."""

    is_correct: bool


# Initialize client for LLM judge (only needed if string matching fails)
api_key = os.getenv("GOOGLE_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)
else:
    print("Warning: GOOGLE_API_KEY not set. LLM judge will not be available.")


ATTACHMENTS_FOLDER_PATH = "benchmark/attachments"


def print_banner(train_number=None):
    """Print the ML6 banner."""
    import pyfiglet
    
    banner = pyfiglet.figlet_format("ML6", font="slant")
    # Orange color using ANSI 256-color code
    orange = "\033[38;5;208m"
    print(f"\n{orange}{Style.BRIGHT}{banner}{Style.RESET_ALL}")
    print(f"{orange}{'=' * 80}{Style.RESET_ALL}")
    if train_number:
        print(
            f"{orange}{Style.BRIGHT}GDG Hackathon - Separate Train File Evaluation (train_{train_number}.json){Style.RESET_ALL}"
        )
    else:
        print(
            f"{orange}{Style.BRIGHT}GDG Hackathon - Separate Train Files Evaluation (All){Style.RESET_ALL}"
        )
    print(f"{orange}{'=' * 80}{Style.RESET_ALL}\n")


def load_train_file(train_number: int):
    """Load a specific train file."""
    dataset_path = f"benchmark/train_{train_number}.json"
    
    try:
        with open(dataset_path, "r") as f:
            data = json.load(f)
            # Handle both array format and dict with "dataset" key
            if isinstance(data, dict) and "dataset" in data:
                return data["dataset"]
            return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Train file not found: {dataset_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in train file: {e}")


def string_match(response: str, expected_answer: str) -> bool:
    """
    Check if response matches expected answer using string comparison.
    Handles both exact matches and partial matches.
    """
    # Exact match
    if response.strip().lower() == expected_answer.strip().lower():
        return True

    return False


def llm_judge(response: str, expected_answer: str, question: str) -> bool:
    """
    Use LLM as a judge to determine if the response is correct.
    Returns a boolean indicating if the response is correct.
    """
    if client is None:
        raise ValueError("GOOGLE_API_KEY not set")
    if response is None or response.strip() == "":
        return False
    prompt = f"""
    You are an evaluation judge.
    Determine if the agent's response is semantically completely equivalent to the expected answer.

Question: {question}

Expected Answer: {expected_answer}

Agent's Response: {response}

Evaluate whether the agent's response is semantically equivalent to the expected answer, even if worded differently.
Be strict but fair - minor variations in wording are acceptable if the core answer is correct.
"""

    try:
        llm_response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": JudgeResponse,
            },
        )

        result: JudgeResponse = llm_response.parsed
        return result.is_correct
    except Exception as e:
        print(f"Error in LLM judge: {e}")
        raise e


def evaluate_single_question(question_data: dict, question_idx: int, train_number: int) -> dict:
    """
    Evaluate a single question.

    Args:
        question_data: Dict containing question, answer, and optional file_name
        question_idx: Index of the question in the dataset
        train_number: The train file number being evaluated

    Returns:
        Dict with evaluation results
    """
    # Extract question and answer based on dataset format
    if "Question" in question_data:  # verbose format
        question = question_data["Question"]
        expected_answer = question_data["Final answer"]
        file_name = question_data.get("file_name", "")
    else:  # simple format
        question = question_data["question"]
        expected_answer = question_data["answer"]
        file_name = question_data.get("file_name", "")

    # Prepare file paths if files are provided
    file_paths = None
    if file_name:
        # Handle comma-separated file names
        files = [f.strip() for f in file_name.split(",") if f.strip()]
        if files:
            file_paths = [os.path.join(ATTACHMENTS_FOLDER_PATH, f) for f in files]

    print(f"\n{Fore.CYAN}{'=' * 80}")
    print(f"{Fore.CYAN}{Style.BRIGHT}Train File {train_number} - Question {question_idx + 1}")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
    question_display = f"{question[:200]}..." if len(question) > 200 else question
    print(f"{Fore.BLUE}{Style.BRIGHT}Question:{Style.RESET_ALL} {question_display}")
    if file_paths:
        print(f"{Fore.MAGENTA}Files:{Style.RESET_ALL} {file_paths}")

    # Run the agent (using USER_ID env var if set, otherwise default "dev_user")
    user_id = os.getenv("USER_ID", "dev_user")
    try:
        start_time = time.time()
        agent_response = server.run_agent(question, file_paths, user_id=user_id)
        end_time = time.time()
        response_time = end_time - start_time

        print(f"\n{Fore.WHITE}Agent Response:{Style.RESET_ALL} {agent_response}")
        print(f"{Fore.YELLOW}Expected Answer:{Style.RESET_ALL} {expected_answer}")
        print(f"{Fore.MAGENTA}Response Time:{Style.RESET_ALL} {response_time:.2f}s")
    except Exception as e:
        print(f"{Fore.RED}Error running agent: {e}{Style.RESET_ALL}")
        raise e

    # First try string matching
    string_matches = string_match(agent_response, expected_answer)

    if string_matches:
        print(f"{Fore.GREEN}{Style.BRIGHT}✓ Correct (string match){Style.RESET_ALL}")
        return {
            "train_file": train_number,
            "question_idx": question_idx,
            "question": question,
            "expected_answer": expected_answer,
            "agent_response": agent_response,
            "correct": True,
            "method": "string_match",
            "response_time": response_time,
        }

    # Fall back to LLM judge
    print(f"\n{Fore.YELLOW}String match failed, using LLM judge...{Style.RESET_ALL}")
    is_correct = llm_judge(agent_response, expected_answer, question)

    if is_correct:
        print(f"{Fore.GREEN}{Style.BRIGHT}✓ Correct (LLM judge){Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}{Style.BRIGHT}✗ Incorrect{Style.RESET_ALL}")

    return {
        "train_file": train_number,
        "question_idx": question_idx,
        "question": question,
        "expected_answer": expected_answer,
        "agent_response": agent_response,
        "correct": is_correct,
        "method": "llm_judge",
        "response_time": response_time,
    }


def evaluate_train_file(train_number: int, output_file=None) -> dict:
    """
    Evaluate a specific train file.

    Args:
        train_number: The train file number (1-10)
        output_file: Optional output file path

    Returns:
        Dict with evaluation results
    """
    # Print the banner
    print_banner(train_number)

    dataset = load_train_file(train_number)

    results = []
    correct_count = 0
    total_count = len(dataset)

    print(
        f"{Fore.CYAN}{Style.BRIGHT}Starting evaluation of train_{train_number}.json ({total_count} question{'s' if total_count != 1 else ''})...{Style.RESET_ALL}"
    )
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")

    for idx, question_data in enumerate(dataset):
        result = evaluate_single_question(question_data, idx, train_number)
        results.append(result)

        if result["correct"]:
            correct_count += 1

    # Calculate accuracy
    accuracy = (correct_count / total_count) * 100 if total_count > 0 else 0

    # Calculate timing statistics
    response_times = [r["response_time"] for r in results]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0

    # Prepare summary
    summary = {
        "timestamp": datetime.datetime.now().isoformat(),
        "train_file": train_number,
        "total_questions": total_count,
        "correct": correct_count,
        "incorrect": total_count - correct_count,
        "accuracy": round(accuracy, 2),
        "average_response_time": round(avg_response_time, 2),
        "results": results,
    }

    # Print summary
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 80}")
    print(f"EVALUATION SUMMARY - train_{train_number}.json")
    print(f"{'=' * 80}{Style.RESET_ALL}")
    print(f"\n{Fore.WHITE}{Style.BRIGHT}Correctness Metrics:{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Total Questions:{Style.RESET_ALL} {total_count}")
    print(f"{Fore.GREEN}Correct:{Style.RESET_ALL} {correct_count}")
    print(f"{Fore.RED}Incorrect:{Style.RESET_ALL} {total_count - correct_count}")
    print(f"{Fore.CYAN}{Style.BRIGHT}Accuracy:{Style.RESET_ALL} {accuracy:.2f}%")
    print(f"\n{Fore.WHITE}{Style.BRIGHT}Timing Metrics:{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Average Response Time:{Style.RESET_ALL} {avg_response_time:.2f}s")
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")

    # Save results to file
    if output_file is None:
        output_file = f"evaluation_train_{train_number}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\n{Fore.CYAN}Results saved to:{Style.RESET_ALL} {output_file}")
    except IOError as e:
        raise IOError(f"Failed to write results to {output_file}: {e}")

    return summary


def evaluate_all_train_files(output_file=None) -> dict:
    """
    Evaluate all train files (train_1.json through train_10.json).

    Args:
        output_file: Optional output file path

    Returns:
        Dict with aggregated results
    """
    print_banner()
    
    all_results = []
    file_summaries = []
    total_correct = 0
    total_questions = 0

    for train_number in range(1, 11):
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}Processing train_{train_number}.json...{Style.RESET_ALL}")
        
        try:
            dataset = load_train_file(train_number)
            
            for idx, question_data in enumerate(dataset):
                result = evaluate_single_question(question_data, idx, train_number)
                all_results.append(result)
                
                if result["correct"]:
                    total_correct += 1
                total_questions += 1
            
            # Calculate per-file stats
            file_correct = sum(1 for r in all_results if r["train_file"] == train_number and r["correct"])
            file_total = len(dataset)
            file_accuracy = (file_correct / file_total * 100) if file_total > 0 else 0
            
            file_summaries.append({
                "train_file": train_number,
                "correct": file_correct,
                "total": file_total,
                "accuracy": round(file_accuracy, 2)
            })
            
        except FileNotFoundError:
            print(f"{Fore.RED}train_{train_number}.json not found, skipping...{Style.RESET_ALL}")
            continue

    # Calculate overall accuracy
    overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0

    # Calculate timing statistics
    response_times = [r["response_time"] for r in all_results]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0

    # Prepare summary
    summary = {
        "timestamp": datetime.datetime.now().isoformat(),
        "overall": {
            "total_questions": total_questions,
            "correct": total_correct,
            "incorrect": total_questions - total_correct,
            "accuracy": round(overall_accuracy, 2),
            "average_response_time": round(avg_response_time, 2),
        },
        "per_file_summary": file_summaries,
        "detailed_results": all_results,
    }

    # Print summary
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'=' * 80}")
    print("OVERALL EVALUATION SUMMARY - All Train Files")
    print(f"{'=' * 80}{Style.RESET_ALL}")
    print(f"\n{Fore.WHITE}{Style.BRIGHT}Overall Metrics:{Style.RESET_ALL}")
    print(f"{Fore.WHITE}Total Questions:{Style.RESET_ALL} {total_questions}")
    print(f"{Fore.GREEN}Correct:{Style.RESET_ALL} {total_correct}")
    print(f"{Fore.RED}Incorrect:{Style.RESET_ALL} {total_questions - total_correct}")
    print(f"{Fore.CYAN}{Style.BRIGHT}Overall Accuracy:{Style.RESET_ALL} {overall_accuracy:.2f}%")
    print(f"{Fore.MAGENTA}Average Response Time:{Style.RESET_ALL} {avg_response_time:.2f}s")
    
    print(f"\n{Fore.WHITE}{Style.BRIGHT}Per-File Breakdown:{Style.RESET_ALL}")
    for file_summary in file_summaries:
        train_num = file_summary["train_file"]
        accuracy = file_summary["accuracy"]
        correct = file_summary["correct"]
        total = file_summary["total"]
        
        if accuracy == 100:
            color = Fore.GREEN
        elif accuracy >= 50:
            color = Fore.YELLOW
        else:
            color = Fore.RED
            
        print(f"{color}train_{train_num}.json:{Style.RESET_ALL} {correct}/{total} correct ({accuracy:.2f}%)")
    
    print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")

    # Save results to file
    if output_file is None:
        output_file = f"evaluation_all_trains_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\n{Fore.CYAN}Results saved to:{Style.RESET_ALL} {output_file}")
    except IOError as e:
        raise IOError(f"Failed to write results to {output_file}: {e}")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Evaluate the agent on individual train files (train_1.json through train_10.json)"
    )
    parser.add_argument(
        "--train",
        type=int,
        choices=range(1, 11),
        metavar="[1-10]",
        help="Specific train file number to evaluate (1-10). If not provided, evaluates all train files.",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path for results. Default: evaluation_train_<number>_<timestamp>.json",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Evaluate all train files (train_1.json through train_10.json)",
    )

    args = parser.parse_args()

    if args.all:
        # Evaluate all train files
        evaluate_all_train_files(output_file=args.output)
    elif args.train is not None:
        # Evaluate specific train file
        evaluate_train_file(args.train, output_file=args.output)
    else:
        # Default: evaluate all train files
        evaluate_all_train_files(output_file=args.output)

