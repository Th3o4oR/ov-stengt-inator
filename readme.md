# Omega Verksted stengt-inator

## Hva er dette?
Prosjektet inneholder kode for en Raspberry Pi Pico W, som vil kunne sjekke om døra til Omega Verksted er åpen eller ikke ved å kalle på en API.

## Fargekoder
- Rød: Døra er stengt
- Grønn: Døra er åpen
- Blinkende gul: API-en er utilgjengelig
- Blå: Pico-en prøver å koble til Wi-Fi for første gang siden oppstart
- Blinkende blå: Pico-en prøver å koble til Wi-Fi etter å ha mistet tilkopling

## Config
For å sette opp config-fila til prosjektet er du kun nødt til å kopiere `config.example.json` til `config.json` og fylle inn de nødvendige feltene.
Nettverkene blir prøvd tilkoplet i alfabetisk rekkefølge, så det kan være lurt å indeksere dem med tall for å få dem i riktig rekkefølge, slik som i eksempelet.
Ikke glem å legge til `config.json` i `.gitignore` for å unngå å legge ut passord og annen sensitiv informasjon på GitHub.

## Annet
Ved å endre navn på `main_file.py` til `main.py` vil Pico-en automatisk kjøre denne fila ved oppstart. Dette er gunstig når koden er ferdig, men kan gjøre det vanskelig å få lastet opp ny kode for å teste. Dersom dette skjer, følg instruksjonene under for såkalt flash-nuking. 

## Flash nuke
Last opp `flash_nuke.uf2` til Pico-en for å slette alle filer og alt av minne på den. 
Filen er hentet fra [adafruit](https://learn.adafruit.com/getting-started-with-raspberry-pi-pico-circuitpython/circuitpython#flash-resetting-uf2-3083182)
