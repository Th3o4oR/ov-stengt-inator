# Omega Verksted stengt-inator

## Hva er dette?
Prosjektet inneholder kode for en Raspberry Pi Pico W, som vil kunne sjekke om døra til Omega Verksted er åpen eller ikke ved å kalle på en API.

## Fargekoder
- Rød: Døra er stengt
- Grønn: Døra er åpen
- Blinkende gul: API-en er utilgjengelig
- Blå: Pico-en prøver å koble til Wi-Fi for første gang siden oppstart
- Blinkende blå: Pico-en prøver å koble til Wi-Fi etter å ha mistet tilkopling

## Flash nuke
Last opp flash_nuke.uf2 til Pico-en for å slette alle filer og alt av minne på den. 
Filen er hentet fra [adafruit](https://learn.adafruit.com/getting-started-with-raspberry-pi-pico-circuitpython/circuitpython#flash-resetting-uf2-3083182)
