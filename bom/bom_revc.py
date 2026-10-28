import csv, json
# (system, part, qty, unit_usd, mass_g_each, basis, fit/notes)
R=[
('Propulsion','T-Motor Velox V2306 V3 1750KV motor (or iFlight XING2 2306 1750KV)',4,29.0,33.8,'iFlight XING2 2306 $28.99 (racedayquads page); T-Motor Velox V3 listed $18.99 but sold out (pyrodrone). Mass: T-Motor page 33.8 g incl. cable','Fits 28x28x31 mm placeholder (16x16 mount, 5 mm shaft)'),
('Propulsion','HQProp DP 5.1x5.1x3 propeller, set of 4 (buy 6 sets)',6,3.99,5.0,'myfpvstore $3.99/set of 4, in stock','127 mm ring clearance: 5.1 in = 129.5 mm, check 4 mm tip gap -> use 5.0 in if rubbing. High-pitch: suits speed mode'),
('Propulsion','SpeedyBee BLS 60A 3-6S 4-in-1 ESC (30.5x30.5 mount)',1,60.0,23.5,'GBP 44.99 incl. VAT at flyingtech.co.uk (~$60); out of stock there; 60 A cont / 80 A burst','Board is 45.6x44 mm: larger than 36x34 stack placeholder, needs ~10 mm more bay in X/Y'),
('Flight control','Holybro Kakute H7 V2 (STM32H743, BMI270, 6 UART) running ArduPilot',1,52.0,8.0,'Holybro store $52, sold out / made to order; Matek H743-Slim V3 $116.49 is the in-stock fallback','35x35 mm, 30.5 mount: fits'),
('Flight control','Matek M10Q-5883 GPS + compass',1,48.0,8.0,'wrekd.com $47.99, pre-order','Fits (22x22x8 vs 28x28x7 placeholder)'),
('Power','Tattu R-Line V5 6S 1400 mAh 150C LiPo',2,55.49,222.0,'getfpv $55.49, 222 g +/-20 g, 78x39x42 mm, in stock','1 pack fits bay (3 mm taller than placeholder, checked against shell). 2nd pack is a spare (not carried together)'),
('Power','12 V 5 A BEC / power board for servo bus',1,15.0,10.0,'ESTIMATE (catalogue class)','Needs space; small'),
('Joints','Feetech STS3215 12 V 30 kg.cm magnetic-encoder servo (J1 and J2, 2 per arm)',8,31.71,55.0,'robotshop $31.71. Mass/size from vendor datasheet (55 g, 45x25x35 mm), not on the page','DOES NOT FIT current arm fairing (about 2x too large). Rev-C arm redesign needed'),
('Joints','Servo bus driver board (Waveshare-class)',1,10.0,10.0,'ESTIMATE','-'),
('Wheel drive','Small brushless 1404-class motor, ~3000 KV, with mini 4-in-1 ESC (4 wheels)',4,25.0,15.0,'ESTIMATE (catalogue class, NOT verified). Low-speed control is the main risk','Replaces 12x12x24 gearmotor placeholder; may need FOC driver instead'),
('Compute','Raspberry Pi Zero 2 W',1,20.0,10.0,'ESTIMATE; Pi 5 4GB would be $85 (TechSpot, Feb 2026) but is far too big','65x30 mm vs 40x34 placeholder: bay change needed. Optional for first flights'),
('Compute','Pi Camera Module 3',1,25.0,4.0,'ESTIMATE','Fits (25x24x12)'),
('Radio','RadioMaster Pocket ELRS transmitter',1,59.99,0.0,'RadioMaster store $59.99 (diyfpv listing)','-'),
('Radio','ExpressLRS 2.4 GHz receiver',1,20.0,2.0,'ESTIMATE','Fits'),
('Airframe','Wing: foam core, carbon spar, film skin (about 400-600 cm2)',1,60.0,120.0,'ESTIMATE; wing CAD not yet drawn','Space between ring pairs limits chord; see notes'),
('Airframe','Printed rings, rims, tyres, arms, shell (PA12-CF / PETG-CF / TPU)',1,200.0,0.0,'ESTIMATE; mass already in CAD (~1.0 kg incl. rings)','-'),
('Airframe','Carbon tube/plate, bearings, hinge pins, fasteners, joint locks',1,120.0,40.0,'ESTIMATE','-'),
('Airframe','Wiring, silicone wire, connectors, XT60, capacitors',1,60.0,60.0,'ESTIMATE','-'),
]
sub=sum(q*p for _,_,q,p,_,_,_ in R)
spares=0.25*sub
tot=sub+spares
with open('CF2_RevC_BOM.csv','w',newline='') as f:
    w=csv.writer(f); w.writerow(['system','part','qty','unit_usd','line_usd','mass_g_each','price_basis','fit_note'])
    for s,p,q,u,m,b,n in R: w.writerow([s,p,q,u,round(q*u,2),m,b,n])
    w.writerow(['','SUBTOTAL','','',round(sub,2)]); w.writerow(['','Spares / crash reserve 25 %','','',round(spares,2)]); w.writerow(['','TOTAL','','',round(tot,2)])
print('subtotal %.0f  spares %.0f  total %.0f'%(sub,spares,tot))
# mass: CAD 1332 g minus placeholders replaced + real parts
cad=1332.0
repl={'rotor motors 4x33':132,'props 4x5':20,'old servos 8x12':96,'old battery':190,'old fc stack':14,'old companion':45,'old camera':22,'old gps':15,'old wheel gearmotor+pinion 4x12':48}
rem=sum(repl.values())
new=4*33.8+4*5+8*55+222+(23.5+8+10)+10+4+8+4*15+10+120+40+60+2+10
print('CAD %.0f - replaced %.0f + real %.0f = %.0f g'%(cad,rem,new,cad-rem+new))
json.dump(dict(subtotal=sub,spares=spares,total=tot,mass_g=cad-rem+new),open('bom_totals.json','w'))
