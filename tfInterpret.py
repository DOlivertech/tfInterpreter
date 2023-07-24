#!/usr/bin/env python3

import openai
import argparse
import textwrap
import keyring
import sys

SERVICE_ID = 'my_application'
USER_ID = 'openai'

TOKEN_LIMIT = 8000


def get_api_key():
    api_key = keyring.get_password(SERVICE_ID, USER_ID)
    if api_key is None:
        print("No API key found. Please enter your OpenAI API key:")
        api_key = input()
        keyring.set_password(SERVICE_ID, USER_ID, api_key)
    return api_key


openai.api_key = get_api_key()


def read_terraform_plan(file_path):
    with open(file_path, 'r') as file:
        data = file.read()
    return data


def split_plan(plan):
    return textwrap.wrap(plan, TOKEN_LIMIT)


def is_relevant(chunk):
    return not chunk.isspace()


def interpret_plan_chunk(chunk, chunk_number, total_chunks):
    print(f"Analyzing chunk {chunk_number} of {total_chunks}...")
    messages = [
        {"role": "system", "content": "You are a helpful assistant that translates Terraform plans into simple terms. You should provide a detailed yet easily understandable explanation of all the changes that will be made, highlighting any additions, deletions, or modifications. Avoid explaining what Terraform is doing or details about the '-out' option. Just state the facts and provide a brief analysis."},
        {"role": "user", "content": f"Please explain this part of the Terraform plan concisely and factually:\n{chunk}"},
        {"role": "user", "content": "What resources will be added, modified, or deleted? Provide a brief and factual explanation."},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=messages,
        max_tokens=TOKEN_LIMIT,
    )

    result = f"Chunk {chunk_number} of {total_chunks}:\n{response['choices'][0]['message']['content'].strip()}\n\n---\nTokens used for this chunk: {response['usage']['total_tokens']}\n---"
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Interpret a Terraform plan output.')
    parser.add_argument(
        'file', type=str, help='The Terraform plan output file.')

    try:
        args = parser.parse_args()
    except SystemExit:
        print("Error: A file argument is required. Please provide the path to the Terraform plan output file as .txt")
        return

    print("Reading and analyzing your plan output...")

    plan = read_terraform_plan(args.file)
    plan_chunks = split_plan(plan)

    print(f"The analysis has been split into {len(plan_chunks)} chunks.")

    interpretations = []
    for i, chunk in enumerate(plan_chunks):
        if is_relevant(chunk):
            interpretations.append(interpret_plan_chunk(
                chunk, i+1, len(plan_chunks)))
        else:
            print(
                f"Skipping chunk {i+1} of {len(plan_chunks)} as it does not contain relevant information.")

    print("\n".join(interpretations))


if __name__ == "__main__":
    main()
