# Comparing attributes from ranker Feature Selection methods (page-based)

def main():
    # 48 features
    # Top 10 from each filter method
    correlation = [48,35,5,39,34,30,1,27,25,40]

    information = [27,28,48,34,14,35,47,5,39,1]

    chi = [27,28,48,34,14,47,35,5,39,1]

    ranked = {}

    for i in range(49):
        if i in correlation:
            if i in information:
                if i in chi:
                    # Check for similarities between the feature selection methods
                    corrStrength = correlation.index(i)
                    infoStrength = information.index(i)
                    chiStrength = chi.index(i)
                    avgIndex = (corrStrength + infoStrength + chiStrength) / 3
                    ranked[i] = avgIndex

    # This outputs the selected features in both lists in rank order, in this context it's [35, 27, 34, 5, 39, 1, 30, 3, 25, 47]
    print(f"{sorted(ranked, key=ranked.get)}")

if __name__ == '__main__':
    main()

# I plan on trying ML a few times, once with the initial list of features, one with this list of features