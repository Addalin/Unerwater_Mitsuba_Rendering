---------------------------------------------------------------
# List of commands to run before operating mitsuba simulation # 
---------------------------------------------------------------

---------------------------------------------------------------
#                      update mitsuba code                    #
---------------------------------------------------------------
cd $MITSUBA_SIM
git pull 

---->
# if not working delete $MITSUBA_SIM and do : 
cd ..
rm -r $MITSUBA_SIM
git clone https://github.com/Addalin/mitsuba_sim.git
cd $MITSUBA_SIM
<----

---------------------------------------------------------------
#                    update configurations                    #
1. create mitsuba_sim_results folder (as saved in environment path !)
2. update: sim_config.yml : scene : bg / cloud , nRuns : 2 
3. update: hetvol.xml : cloud_water_green.vol / cubic_water_green.vol
4. update: sensorName in main_mitsuba_sim.py
5. update: maxThreads in mitsubaWrapperLib.py - according to cores availability
---------------------------------------------------------------

mkdir mitsuba_sim_results
pico sim_config.yml
pico 3D_models/hetvol/mitsuba/hetvol.xml
pico main_mitsuba_sim.py
pico mitsubaWrapperLib.py

---------------------------------------------------------------
#                     run simulation                          #
---------------------------------------------------------------
python main_mitsuba_sim.py |& tee -a output.txt
