import re

text = '''
TELEKOMÜNİKASYON
Türk Telekom
Türk Telekom International
Turkcell
Turkcell Teknoloji
Vodafone Türkiye
Vodafone Teknoloji
TürkNet
Superonline
Netaş
Karel
Ericsson Türkiye
Nokia Türkiye
Huawei Türkiye
TT Ventures
Türksat
Türksat Bilişim

OTOMOTİV
Toyota
tofas
Mercedes

BANKA VE FİNANS
Garanti BBVA
Garanti BBVA Teknoloji
Yapı Kredi
Yapı Kredi Teknoloji
Akbank
Akbank Teknoloji
İş Bankası
Softtech
Ziraat Bankası
Ziraat Teknoloji
VakıfBank
VakıfBank BT
Halkbank
TEB
QNB Türkiye
DenizBank
ING Türkiye
Fibabanka
Odeabank
Alternatif Bank
Türkiye Finans
Kuveyt Türk
Albaraka Türk
Türk Eximbank
Merkez Bankası
Borsa İstanbul

FİNTEK
Papara
BtcTurk
iyzico
Param
Moka
Sipay
Colendi
United Payment
Hepsipay
Paycell
Sigortam.net

E-TİCARET VE DİJİTAL
Trendyol
Trendyol Tech
Hepsiburada
Hepsiburada Teknoloji
Getir
Yemek sepeti
Sahibinden
Akakçe
ÇiçekSepeti
n11
Dolap
Sezzle
Modanisa

OYUN
Peak Games
Dream Games
Rollic
Gram Games
Spyke Games
Good Job Games
Ace Games
Masomo
Loop Games

YAZILIM VE TEKNOLOJİ
OBSS
Etiya
Logo Yazılım
Architecht
Innova
KoçSistem
Bimser
Mia Teknoloji
Hitit
Commencis
Sestek
CBOT
Vispera
Peoplise
NTT DATA Türkiye
IBM Türkiye
Oracle Türkiye
Microsoft Türkiye
SAP Türkiye
Siemens Türkiye
Schneider Electric Türkiye
Bosch Türkiye
Accenture Türkiye
CGI Türkiye
DefineX
VeriPark
ICterra
BilgeAdam Teknoloji
ATP Yazılım
OBASE
Akinon
Insider
Usersdot
Related Digital
Segmentify
SmartIQ
Fineksus
Intertech
Netsis

SİBER GÜVENLİK
Picus Security
Cyberwise
Biznet
Berqnet
Kron Teknoloji
Procenne
STM Siber Güvenlik
Labris Networks

GLOBAL TEKNOLOJİ ŞİRKETLERİ
Google Türkiye
Amazon Türkiye
AWS Türkiye
Meta Türkiye
Apple Türkiye
Intel Türkiye
AMD Türkiye
Dell Technologies
HP Enterprise
Lenovo Türkiye
Red Hat Türkiye
Palo Alto Networks
Fortinet
Trend Micro
Check Point
Salesforce
ServiceNow

DANIŞMANLIK
Deloitte
PwC
EY
KPMG

HOLDİNGLER
Koç Holding
Sabancı Holding
Eczacıbaşı Holding
Anadolu Grubu
Borusan Holding
Doğuş Holding
Zorlu Holding
Yıldız Holding
Alarko Holding
Limak Holding
Kalyon Holding
Rönesans Holding
Karadeniz Holding
FuzulEv
IC Holding
Tekfen Holding
Cengiz Holding

SANAYİ VE ÜRETİM
Şişecam
Tüpraş
Petkim
Ford Otosan
Tofaş
Mercedes-Benz Türk
Toyota Otomotiv Türkiye
Hyundai Motor Türkiye
Oyak Renault
oyak çimento adana
Anadolu Isuzu
TEMSA
Karsan
TürkTraktör
Arçelik
Beko
Vestel
Vestel Elektronik
Vestel Beyaz Eşya
Profilo
Grundig
Sunny Elektronik
Ereğli Demir Çelik (ERDEMİR)
İskenderun Demir Çelik (İSDEMİR)
Kastamonu Entegre
Kale Grubu
Kordsa
Brisa
Akçansa
Çimsa
Kardemir
Türk Prysmian Kablo
Sarkuysan
Kontrolmatik
Astor Enerji
Europower
CW Enerji
Smart Güneş
Alfa Solar
Kimpur
SASA Polyester
Aksa Akrilik
Eti Bakır
Koluman Holding
delphi

OTOMOTİV YAN SANAYİ
Bosch
Continental
Valeo
ZF Türkiye
Yazaki
Farplas
Assan Hanil
Coşkunöz Holding
Martur

ENERJİ
Enerjisa
Enerjisa Üretim
Aksa Enerji
Zorlu Enerji
SOCAR Türkiye
Shell Türkiye
BP Türkiye
Petrol Ofisi
OPET
TotalEnergies Türkiye
ExxonMobil Türkiye
Chevron Türkiye
Aytemiz
EPİAŞ
TEİAŞ
BOTAŞ
EÜAŞ
TPAO
Başkentgaz
İGDAŞ
ENKA
Gama Enerji
IC İçtaş Enerji

FMCG VE GIDA
Eti
Ülker
Pınar
Coca-Cola İçecek
Migros
Şok Marketler
BİM
A101
CarrefourSA

PERAKENDE
LC Waikiki
Boyner
Mavi
DeFacto
FLO
Gratis
Teknosa

LOJİSTİK
Aras Kargo
MNG Kargo
Yurtiçi Kargo
Sürat Kargo

HAVACILIK VE ULAŞIM
Türk Hava YollarıF
Turkish Technology
Pegasus
SunExpress
TAV Havalimanları
TAV Technologies
TCDD Taşımacılık

KAMU VE TEKNOLOJİ
TÜBİTAK
TÜBİTAK BİLGEM
TÜBİTAK SAGE
TÜBİTAK UZAY
BTK
TÜRKSAT
PTT
PTT Bilgi Teknolojileri
TAKBİS
Profen

SAĞLIK VE İLAÇ
Abdi İbrahim
Deva Holding
Nobel İlaç
Santa Farma
Bayer Türkiye
Pfizer Türkiye
Roche Türkiye
Novartis Türkiye
Sanofi Türkiye
MSD Türkiye
AstraZeneca Türkiye
Acıbadem Sağlık Grubu
Memorial Sağlık Grubu
Medical Park

SAVUNMA VE HAVACILIK
ASELSAN
TUSAŞ (TAI)
TEI
ROKETSAN
HAVELSAN
STM
FNSS
BMC
Baykar
MKE
Meteksan Savunma
SDT Uzay ve Savunma
MilSOFT
Otokar
CTech
Lentatek
DeltaV Uzay
Kale Arge
Kale Havacılık
Alp Havacılık
Coşkunöz Savunma
Repkon
TÜBİTAK SAGE
TÜBİTAK UZAY
TÜBİTAK BİLGEM
'''

headers = [
    'TELEKOMÜNİKASYON', 'OTOMOTİV', 'BANKA VE FİNANS', 'FİNTEK', 
    'E-TİCARET VE DİJİTAL', 'OYUN', 'YAZILIM VE TEKNOLOJİ', 'SİBER GÜVENLİK', 
    'GLOBAL TEKNOLOJİ ŞİRKETLERİ', 'DANIŞMANLIK', 'HOLDİNGLER', 'SANAYİ VE ÜRETİM',
    'OTOMOTİV YAN SANAYİ', 'ENERJİ', 'FMCG VE GIDA', 'PERAKENDE', 'LOJİSTİK',
    'HAVACILIK VE ULAŞIM', 'KAMU VE TEKNOLOJİ', 'SAĞLIK VE İLAÇ', 'SAVUNMA VE HAVACILIK'
]

headers_lower = set(h.lower() for h in headers)
lines = text.split('\n')
companies = []
seen = set()

for line in lines:
    line = line.strip()
    if not line:
        continue
    if line.lower() in headers_lower:
        continue
    
    lower_line = line.lower().replace('ı', 'i').replace('i̇', 'i').replace('ş', 's').replace('ç', 'c').replace('ğ', 'g').replace('ö', 'o').replace('ü', 'u')
    if lower_line not in seen:
        seen.add(lower_line)
        companies.append(line)

with open('deduplicated_companies.txt', 'w', encoding='utf-8') as f:
    for c in companies:
        f.write(c + '\n')
print(f'Total unique companies: {len(companies)}')
