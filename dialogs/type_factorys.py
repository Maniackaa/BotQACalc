def positive_int_check(text: str) -> str:
    if all(ch.isdigit() for ch in text) and 0 <= int(text):
        return text
    raise ValueError


def tel_check(text: str) -> str:
    digits = [x for x in text if x.isdigit()]
    if len(digits) < 5 or len(digits) > 12:
        raise ValueError
    return text

cars = """Toyota
Лада
Volkswagen
Nissan
Kia
Hyundai
Honda
Mutsubishi
Mercedes-Benz
BMW
Mazda
Ford
Chevrolet
Renault
Lexus
Subaru
Audi
Skoda
Opel
Chery
УАЗ
ЛУАЗ
ГАЗ
ТагАЗ
Suzuki
Haval
Land Rover
Peugeot
Daewoo
Infiniti
Gelly
Exeed
Volvo
Daihatsu
Citroen
Ssang Yong
Porsche
Lifan
Omoda
Jeep
ЗАЗ
Datsun
Great Wall
Changan
МОСКВИЧ
Cadilac
Fiat
Dodge
Mini
Genesis
ИЖ
Jaguar
Chrysler
Isuzu
Evolute
FAW
Smart
Vortex
Acura
Tesla
Hummer
JAC
SEAT
Ravon
Lincoln
Dongfeng
BYD"""
carlist = cars.split('\n')
print(carlist)