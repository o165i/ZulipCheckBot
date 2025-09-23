
adressbuch = []
while True:
    print("Menu: ")
    print("1. Kontakt hinzufügen.")
    print("2. Kontakte anzeigen.")
    print("3. Nachname suchen.")
    print("4. Kontakt löschen.")
    print("5. Beenden.")
    wahl = input("Ihre wahl (1-5) ")

    if wahl == "1":
        print("\n Neuer Kontakt ")
        name = input("Name: ")
        telefon = input("Telefonnummer: ")
        email = input("E-Mail: ")
        
        kontakt = {
            "Name": name,
            "Telefon": telefon,
            "E-Mail": email
        }
        adressbuch.append(kontakt)
        print(f"Kontakt '{name}' wurde hinzugefügt!")
    elif wahl == "2":
        print("\n Alle Kontakte ")
        if not adressbuch:
            print("Adressbuch ist Leer")
        else:
            for x, kontakt in enumerate(adressbuch, 1):
                print(f"{x}. {kontakt['Name']} - {kontakt['Telefon']} - {kontakt['E-Mail']}")
    elif wahl == "3":
        print("\n Kontakt Suchen ")
        such_name = input("Geben Sie den Namen ein. ")
        gefunden = False
        for kontakt in adressbuch:
            if kontakt["Name"].lower() == such_name.lower():
                print(f"Gefunden: {kontakt['Name']} - {kontakt['Telefon']} - {kontakt['E-Mail']}")
                gefunden = True
            if not gefunden:
                print("Kontakt war nicht gefunden")
    elif wahl == "4":
        print("\n Kontakt Löschen ")
        if not adressbuch:
            print("Adressbuch ist Leer.")
        else:
            for i, kontakt in enumerate(adressbuch, 1):
                print(f"{i}, {kontakt['Name']}")
            try:
                nummer = int(input("Welche Nummer löschen? (0 zum Abbrechen): "))
                if nummer == 0:
                    print("Löschen abgebrochen")
                elif 1 <= nummer <= len(adressbuch):
                    gelöscht = adressbuch.pop(nummer - 1)
                    print(f"Kontakt '{gelöscht['Name']}' wurde gelöscht.")
                else:
                    print("Ungültige Nummer.")
            except ValueError:
                print("Bitte eine Zahl eingeben")
    elif wahl == "5":
        print("Programme beenden")
        break
    else:
        print("Ungültige Wahl. Bitte 1-5 eingeben.")
    
                