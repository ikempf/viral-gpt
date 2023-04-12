#!/usr/bin/env python3
import json
import os
import sys
import time
import subprocess

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

print("\033[96m\033[1m" + "\n*****Website Under Test*****\n" + "\033[0m\033[0m")
print(URL)

while True:
    command = command_creation_agent()

    print(f"\033[93m\033[1m" + f"\n*****Verification n.{VERIFICATIONS}*****" + "\033[0m\033[0m")
    print(f"Command: {bold(command.cmd)}")
    print(f"Explanation: {command.explanation}")

    input("\nPress Enter to run the command...")

    print(f"Running command {bold(command.cmd)}")
    stream = subprocess.run(command.cmd, capture_output=True, shell=True)
    output = stream.stdout.decode("utf-8") + " " + stream.stderr.decode("utf-8")
    print(f"Results for {bold(command.cmd)}")
    print(output[:50])

    print("\033[93m\033[1m" + "\n*****Verification Result*****" + "\033[0m\033[0m")
    assessment = command_evaluation_agent(output)
    print(assessment)

    price = (TOKEN_USAGE / 1000) * 0.002
    print(f"Total tokens used {bold(TOKEN_USAGE)}. Cost estimation: {bold(price)}$")

    time.sleep(10)
    VERIFICATIONS = VERIFICATIONS + 1
