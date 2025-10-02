from gemini_client import ask_gemini

if __name__ == "__main__":
    answer = ask_gemini("Say hello in 2 short sentences.")
    print(answer)
