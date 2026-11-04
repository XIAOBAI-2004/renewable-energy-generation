function build_course_model
root=fileparts(mfilename('fullpath'));
cacheRoot=getenv('COURSE_TEMP_DIR');
if isempty(cacheRoot),cacheRoot='/temp';end
cache=fullfile(cacheRoot,'renewable-energy','course-project');
Simulink.fileGenControl('set','CacheFolder',fullfile(cache,'simulink'),'CodeGenFolder',fullfile(cache,'codegen'),'createDir',true);
oldVisibility=get(0,'DefaultFigureVisible');
restoreVisibility=onCleanup(@() set(0,'DefaultFigureVisible',oldVisibility));
set(0,'DefaultFigureVisible','off');
m='WindPVStorage_AC_Island'; if bdIsLoaded(m),close_system(m,0);end
new_system(m); load_system('simulink');
set_param(m,'SolverType','Fixed-step','Solver','FixedStepDiscrete','FixedStep','1e-4', ...
    'StopTime','48','SaveOutput','off','SaveTime','off','ReturnWorkspaceOutputs','on', ...
    'SimulationMode','normal','Location',[50 50 1500 900]);
pg=add_block('spspowerguiLib/powergui',[m '/powergui'],'Position',[40 30 160 70]);
set_param(pg,'SimulationMode','Discrete','SampleTime','1e-4','frequency','50','frequencyindice','50','fundamental','50');
add_block('simulink/Sources/Digital Clock',[m '/Time'],'SampleTime','1e-4','Position',[50 740 90 770]);
add_block('simulink/Sources/Constant',[m '/Secondary_control'],'Value','1','Position',[140 740 180 770]);
add_block('simulink/Sources/Constant',[m '/Ts'],'Value','1e-4','Position',[230 740 270 770]);
ctrl=[m '/Wind_PV_BESS_coordination'];add_block('simulink/User-Defined Functions/MATLAB Function',ctrl,'Position',[380 590 670 820]);
rt=sfroot;ch=rt.find('-isa','Stateflow.EMChart','Path',ctrl);ch.Script=fileread(fullfile(root,'course_controller.m'));
add_line(m,'Time/1','Wind_PV_BESS_coordination/1','autorouting','on');
add_line(m,'Secondary_control/1','Wind_PV_BESS_coordination/7','autorouting','on');
add_line(m,'Ts/1','Wind_PV_BESS_coordination/8','autorouting','on');
pv=make_source(m,'PV_5MW_6MVA',false,[60 130 260 210]);
wi=make_source(m,'Wind_5MW_5p5MVA',false,[60 290 260 370]);
ba=make_source(m,'BESS_5MW_10MWh_6MVA',true,[60 450 260 530]);
sources={pv,wi,ba}; meters=cell(1,3);
for k=1:3
    meters{k}=add_block(sprintf('spsThreePhaseVIMeasurementLib/Three-Phase\nV-I Measurement'),[m sprintf('/Meter_%d',k)],'Position',[320 130+160*(k-1) 350 210+160*(k-1)]);
    p=get_param(sources{k},'PortHandles');q=get_param(meters{k},'PortHandles');
    for j=1:3,add_line(m,p.RConn(j),q.LConn(j),'autorouting','on');end
    add_line(m,['Wind_PV_BESS_coordination/' num2str(k)],[get_param(sources{k},'Name') '/1'],'autorouting','on');
end
loadmeter=add_block(sprintf('spsThreePhaseVIMeasurementLib/Three-Phase\nV-I Measurement'),[m '/Meter_load'],'Position',[740 290 770 370]);
lp=get_param(loadmeter,'PortHandles');bp=get_param(meters{1},'PortHandles');
for j=1:3
    add_line(m,bp.RConn(j),lp.LConn(j),'autorouting','on');
    for k=2:3,q=get_param(meters{k},'PortHandles');add_line(m,q.RConn(j),lp.LConn(j),'autorouting','on');end
end
loadgroup=make_loads(m,[900 250 1150 430]);q=get_param(loadgroup,'PortHandles');
for j=1:3,add_line(m,lp.RConn(j),q.LConn(j),'autorouting','on');end
% Small physical shunt capacitance at the AC bus, 0.2 MVAr at 11 kV.
cap=add_block(sprintf('spsThreePhaseParallelRLCLoadLib/Three-Phase\nParallel RLC Load'),[m '/Bus_filter_C'],'Position',[570 120 650 200]);
set_param(cap,'NominalVoltage','11000','NominalFrequency','50','ActivePower','0','InductivePower','0','CapacitivePower','2e5');
cm=add_block(sprintf('spsThreePhaseVIMeasurementLib/Three-Phase\nV-I Measurement'),[m '/Meter_cap'],'Position',[510 120 540 200]);
q=get_param(cap,'PortHandles');cp=get_param(cm,'PortHandles');
for j=1:3,add_line(m,lp.LConn(j),cp.LConn(j),'autorouting','on');add_line(m,cp.RConn(j),q.LConn(j),'autorouting','on');end
add_block('simulink/Discrete/Unit Delay',[m '/Measurement_delay_6'],'SampleTime','1e-4','InitialCondition','[0 0 0]','Position',[1220 560 1265 590]);
add_line(m,'Meter_cap/2','Measurement_delay_6/1','autorouting','on');add_line(m,'Measurement_delay_6/1','Wind_PV_BESS_coordination/9','autorouting','on');
add_block('simulink/Sinks/Terminator',[m '/unused_cap_v'],'Position',[555 90 575 110]);add_line(m,'Meter_cap/1','unused_cap_v/1');
inputs={'Meter_load/1','Meter_1/2','Meter_2/2','Meter_3/2','Meter_load/2'};
for k=1:5
    nm=sprintf('Measurement_delay_%d',k);
    add_block('simulink/Discrete/Unit Delay',[m '/' nm],'SampleTime','1e-4','InitialCondition','[0 0 0]','Position',[760+90*(k-1) 560 805+90*(k-1) 590]);
    add_line(m,inputs{k},[nm '/1'],'autorouting','on');add_line(m,[nm '/1'],['Wind_PV_BESS_coordination/' num2str(k+1)],'autorouting','on');
end
add_block('simulink/Sinks/To Workspace',[m '/Results'],'VariableName','course_results','SaveFormat','Timeseries','Decimation','10','MaxDataPoints','inf','Position',[800 720 940 760]);
add_line(m,'Wind_PV_BESS_coordination/4','Results/1','autorouting','on');
for k=1:3,add_block('simulink/Sinks/Terminator',[m sprintf('/unused_v_%d',k)],'Position',[365 100+160*(k-1) 385 120+160*(k-1)]);add_line(m,sprintf('Meter_%d/1',k),sprintf('unused_v_%d/1',k));end
note=Simulink.Annotation(m,sprintf('11 kV / 50 Hz islanded AC microgrid\nPV: 5 MW, PF=0.9 (positive Q); Wind: 5 MW\nBESS: 5 MW / 10 MWh, 6 MVA, SOC0=60%%\nThree-phase averaged converters; no external grid\nLoad +2 MW @6s; irradiance -30%% @12s; wind -5%% @18s\nLoad -3 MW @24s; irradiance/wind restore @30/36s; Q +1 MVAr @42s'));
note.Position=[860 60];note.FontSize=12;
save_system(m,fullfile(root,[m '.slx']));
fprintf('BUILD_COMPLETE %s\n',fullfile(root,[m '.slx']));close_system(m,0);
end
function s=make_source(m,name,isVoltage,pos)
s=[m '/' name];add_block('built-in/Subsystem',s,'Position',pos);
add_block('simulink/Ports & Subsystems/In1',[s '/abc_command'],'Position',[25 25 55 45]);
add_block('simulink/Signal Routing/Demux',[s '/Demux'],'Outputs','3','Position',[90 20 95 190]);add_line(s,'abc_command/1','Demux/1');
for j=1:3
    nm=['phase_' char('A'+j-1)];
    if isVoltage, lib='spsControlledVoltageSourceLib/Controlled Voltage Source';else,lib='spsControlledCurrentSourceLib/Controlled Current Source';end
    b=add_block(lib,[s '/' nm],'Position',[150 60*j 200 60*j+30]);set_param(b,'Initialize','off');
    add_line(s,['Demux/' num2str(j)],[nm '/1']);
    g=add_block('spsGroundLib/Ground',[s sprintf('/ground%d',j)],'Position',[235 60*j+40 255 60*j+60]);
    c=add_block('built-in/PMIOPort',[s '/' char('A'+j-1)],'Port',num2str(j),'Side','Right','Position',[380 60*j 410 60*j+20]);
    p=get_param(b,'PortHandles');q=get_param(g,'PortHandles');r=get_param(c,'PortHandles');
    % Voltage positive terminal at LConn; current positive flows LConn -> RConn.
    if isVoltage
        add_line(s,p.RConn(1),q.LConn(1));
        rl=add_block('spsSeriesRLCBranchLib/Series RLC Branch',[s sprintf('/filter%d',j)],'Position',[270 60*j 330 60*j+25]);
        set_param(rl,'BranchType','RL','Resistance','.15','Inductance','.003');u=get_param(rl,'PortHandles');
        add_line(s,p.LConn(1),u.LConn(1));add_line(s,u.RConn(1),r.RConn(1));
    else
        add_line(s,p.LConn(1),q.LConn(1));add_line(s,p.RConn(1),r.RConn(1));
    end
end
end
function s=make_loads(m,pos)
s=[m '/Loads'];add_block('built-in/Subsystem',s,'Position',pos);
ports=zeros(1,3);
for j=1:3,c=add_block('built-in/PMIOPort',[s '/' char('A'+j-1)],'Port',num2str(j),'Side','Left','Position',[25 100*j 55 100*j+20]);p=get_param(c,'PortHandles');ports(j)=p.RConn(1);end
P=[7e6,3e6,2e6,0];Q=[2e6,.3e6,.2e6,1e6];times=[0,24,6,42];states={'closed','closed','open','open'};
for k=1:4
    b=add_block(sprintf('spsThreePhaseParallelRLCLoadLib/Three-Phase\nParallel RLC Load'),[s sprintf('/Load_%d',k)],'Position',[400 100*k 470 100*k+70]);
    set_param(b,'NominalVoltage','11000','NominalFrequency','50','ActivePower',num2str(P(k)),'InductivePower',num2str(Q(k)),'CapacitivePower','0');p=get_param(b,'PortHandles');
    if k==1
        for j=1:3,add_line(s,ports(j),p.LConn(j),'autorouting','on');end
    else
        sw=add_block('spsThreePhaseBreakerLib/Three-Phase Breaker',[s sprintf('/Switch_%d',k)],'Position',[220 100*k 270 100*k+70]);
        set_param(sw,'InitialState',states{k},'SwitchTimes',num2str(times(k)),'BreakerResistance','.001','SnubberResistance','1e8','SnubberCapacitance','inf');q=get_param(sw,'PortHandles');
        for j=1:3,add_line(s,ports(j),q.LConn(j),'autorouting','on');add_line(s,q.RConn(j),p.LConn(j),'autorouting','on');end
    end
end
end
