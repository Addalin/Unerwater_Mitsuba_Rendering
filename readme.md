Citation
---
This work is part of simulations done in 

Adi Vainiger, Yoav Y. Schechner, Tali Treibitz, Aviad Avni, and David S. Timor, "Optical wide-field tomography of sediment resuspension," Opt. Express 27, A766-A778 (2019)
https://opg.optica.org/oe/abstract.cfm?uri=oe-27-12-a766

This repo relies on [Mitsuba 0.6](https://github.com/mitsuba-renderer/mitsuba) rendering project .

[//]: < --------------------------------------------------------------->

[//]: < List of commands to run before operating mitsuba simulation > 
[//]: <                    update mitsuba code    >                
[//]: <  cd $MITSUBA_SIM >
[//]: < git pull >

[//]: < ### if not working delete $MITSUBA_SIM and do : >
[//]: < cd ..>

[//]: < rm -r $MITSUBA_SIM>

[//]: < git clone https://github.com/Addalin/Unerwater_Mitsuba_Rendering.git >

[//]: < cd $MITSUBA_SIM >



---------------------------------------------------------------
##                    update configurations                 
1. create mitsuba_sim_results folder (make a similar variable in environment path )
2. update: sim_config.yml : scene : bg / cloud , nRuns : 2 
3. update: hetvol.xml : cloud_water_green.vol / cubic_water_green.vol
4. update: sensorName in main_mitsuba_sim.py
5. update: results_log.csv

---------------------------------------------------------------

mkdir mitsuba_sim_results

pico sim_config.yml

pico 3D_models/hetvol/mitsuba/hetvol.xml

pico main_mitsuba_sim.py

aws s3 sync . "s3://addaline-data/mitsuba_sim_results/resolution 2464 X 2056" --exclude="*" --include="results_log.csv" --include="s3://addaline-
data/mitsuba_sim_results/resolution 2464 X 2056/output*.txt"

mv ./resolution 2464 X 2056/results_log.csv .

rm -r ./resolution 2464 X 2056/`

---------------------------------------------------------------
##                     run simulation                          #
---------------------------------------------------------------
`python main_mitsuba_sim.py |& tee -a output_machineType_sensorType_date.txt`
