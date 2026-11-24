def merge(list1, list2):
    pointer1 = 0
    pointer2 = 0
    temp = []
    # [1, 2, 3, 4, 5, 9, 10]
    while pointer1 < len(list1) and pointer2 < len(list2):
        if list1[pointer1] < list2[pointer2]:
            temp.append(list1[pointer1])
            pointer1 += 1
        else:
            temp.append(list2[pointer2])
            pointer2 += 1

    temp.extend(list1[pointer1:])
    temp.extend(list2[pointer2:])

    return temp

# if __name__ == "__main__":
print(merge([1,4,5,10,11,12,13], [2,3,6,9]))
    