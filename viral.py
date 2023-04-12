#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
import textwrap

import openai
from dotenv import load_dotenv


class Command(object):
    def __init__(self, cmd, explanation):
        self.cmd = cmd
        self.explanation = explanation


def openai_call(prompt: str, temperature: float = 0.5, max_tokens: int = 100):
    response = openai.ChatCompletion.create(
        model=OPENAI_API_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
        n=1,
        stop=None,
    )
    global TOKEN_USAGE
    TOKEN_USAGE = TOKEN_USAGE + response.usage.total_tokens
    return response.choices[0].message.content.strip()


def command_creation_agent():
    prompt = f"""You are a cybersecurity AI that is assessing the security of the following website: {URL}. You 
    respond with a machine-parseable single json body containing exactly one command and description. The json must 
    have the following format : {{command: <command>, explanation: <explanation of the command> }}. I will execute 
    the provided command on my machine the terminal of my macOS machine and the result will be given back to you for 
    assessment."""
    response = openai_call(prompt)
    parsed = json.loads(response)
    return Command(parsed['command'], parsed['explanation'])


def command_evaluation_agent(result: str):
    prompt = f"""Here is the result of the command you provided: {result}. Asses the results in a concisely"""
    response = openai_call(prompt)
    return response


def bold(string: str):
    return f"\033[1m{string}\033[0m"


def price_estimate():
    unit_cost = \
        0.002 if OPENAI_API_MODEL == "gpt-3.5-turbo" else 0.03 if OPENAI_API_MODEL == "gpt-4" else 0.06
    price = (TOKEN_USAGE / 1000) * unit_cost
    return f"{price}$"


TOKEN_USAGE = 0
VERIFICATIONS = 1

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"
openai.api_key = OPENAI_API_KEY

OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
assert OPENAI_API_MODEL, "OPENAI_API_MODEL environment variable is missing from .env"

assert len(sys.argv) == 2, "Provide target URL as parameter"
URL = sys.argv[1]

print(f"\033[96m{bold('*****Website Under Test*****')}\033[0m")
print(URL)

while True:
    command = command_creation_agent()

    print(f"\033[93m\n{bold(f'*****Verification Nb.{VERIFICATIONS}*****')}\033[0m")
    print(f"Command: {bold(command.cmd)}")
    print(f"Explanation: {command.explanation}")
    input("Press Enter to run the command...")

    print(f"Running command {bold(command.cmd)}")
    stream = subprocess.run(command.cmd, capture_output=True, shell=True)
    output = stream.stdout.decode("utf-8") + " " + stream.stderr.decode("utf-8")
    print(f"Results for {bold(command.cmd)}")
    print(textwrap.shorten(output, width=100, placeholder="..."))

    print(f"\033[93m{bold('*****Verification Result*****')}\033[0m")
    assessment = command_evaluation_agent(output)
    print(assessment)

    print(f"{bold('Summary')}: Total tokens used {str(TOKEN_USAGE)}. Cost estimation: {bold(price_estimate())}")

    time.sleep(10)
    VERIFICATIONS = VERIFICATIONS + 1
