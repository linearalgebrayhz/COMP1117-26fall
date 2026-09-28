def count_vowels(text):
    count = 0

    for ch in text:
        if ch == "a" or "e" or "i" or "o" or "u":
            count += 1

    return count

word = "hello"
print(count_vowels(word))