function run_course_case(caseName,stopTime,Ts)
if nargin<1,caseName='coordinated';end
if nargin<2,stopTime=48;end
if nargin<3,Ts=1e-4;end
root=fileparts(mfilename('fullpath'));outdir=fullfile(root,'results',caseName);if ~exist(outdir,'dir'),mkdir(outdir);end
cacheRoot=getenv('COURSE_TEMP_DIR');
if isempty(cacheRoot),cacheRoot='/temp';end
cache=fullfile(cacheRoot,'renewable-energy','course-project');
Simulink.fileGenControl('set','CacheFolder',fullfile(cache,'simulink'),'CodeGenFolder',fullfile(cache,'codegen'),'createDir',true);
diary(fullfile(outdir,'simulation.log'));c=onCleanup(@() diary('off'));
oldVisibility=get(0,'DefaultFigureVisible');restoreVisibility=onCleanup(@() set(0,'DefaultFigureVisible',oldVisibility));
set(0,'DefaultFigureVisible','off');m='WindPVStorage_AC_Island';load_system(fullfile(root,[m '.slx']));cl=onCleanup(@() close_system(m,0));
set_param(m,'StopTime',num2str(stopTime),'FixedStep',num2str(Ts));
set_param([m '/powergui'],'SampleTime',num2str(Ts));set_param([m '/Ts'],'Value',num2str(Ts));set_param([m '/Time'],'SampleTime',num2str(Ts));
for k=1:6,set_param([m sprintf('/Measurement_delay_%d',k)],'SampleTime',num2str(Ts));end
secondary=~strcmp(caseName,'primary_only');set_param([m '/Secondary_control'],'Value',num2str(secondary));
fprintf('START case=%s stop=%g step=%g MATLAB=%s\n',caseName,stopTime,Ts,version);
tic;simout=sim(m);elapsed=toc;
r=simout.course_results;
if r.IsTimeFirst,data=reshape(r.Data,numel(r.Time),[]);else,data=reshape(r.Data,[],numel(r.Time)).';end
names={'P_pv_W','Q_pv_var','P_wind_W','Q_wind_var','P_bess_W','Q_bess_var','P_load_W','Q_load_var','frequency_Hz','voltage_pu','vsg_frequency_Hz','SOC','PV_PF','P_bess_ref_W','E_bess_pu','irradiance_W_m2','wind_m_s','P_pv_available_W','P_wind_available_W','I_bess_rms_A','I_pv_rms_A','I_wind_rms_A','P_balance_W','Q_balance_var','P_battery_DC_W','current_limit_active','Va_V','Vb_V','Vc_V','Ipv_a_A','Ipv_b_A','Ipv_c_A','Ib_a_A','Ib_b_A','Ib_c_A','P_filter_W','Q_filter_var'};
T=array2table([r.Time data],'VariableNames',[{'time_s'} names]);writetable(T,fullfile(outdir,'results.csv'));
save(fullfile(outdir,'simulation_output.mat'),'simout','elapsed','Ts','secondary','-v7.3');
info=struct('case',caseName,'stop_time',stopTime,'step_s',Ts,'elapsed_s',elapsed,'secondary',secondary,'model',m,'matlab',version);
fid=fopen(fullfile(outdir,'run_info.json'),'w');fprintf(fid,'%s',jsonencode(info,PrettyPrint=true));fclose(fid);
fprintf('COMPLETED elapsed=%.2f rows=%d\n',elapsed,height(T));
if stopTime>=2
 q=T.time_s>max(1,stopTime-.5);disp(varfun(@mean,T(q,{'P_pv_W','Q_pv_var','P_wind_W','P_bess_W','frequency_Hz','voltage_pu','PV_PF'})));
end
end
