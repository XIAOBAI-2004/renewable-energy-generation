function start_demo(mode,cacheRoot)
% One command to simulate all three cases and show results. Python is optional.
if nargin<1,mode='run';end
root=fileparts(mfilename('fullpath'));addpath(root);
if strcmpi(mode,'show'),show_results;return;end
if ~strcmpi(mode,'run'),error('Use start_demo or start_demo(''show'').');end
if nargin<2 || isempty(cacheRoot)
    cacheRoot=getenv('COURSE_TEMP_DIR');
    if isempty(cacheRoot),cacheRoot='/temp';end
end
if ~exist(cacheRoot,'dir')
    [ok,msg]=mkdir(cacheRoot);
else
    ok=true;msg='';
end
if ~ok
    if usejava('desktop')
        cacheRoot=uigetdir(root,'请选择用于本次仿真的可写缓存目录');
        if isequal(cacheRoot,0),error('No cache directory selected.');end
    else
        error('Cannot create cache directory: %s. Set COURSE_TEMP_DIR to a writable absolute path.',msg);
    end
end
setenv('COURSE_TEMP_DIR',cacheRoot);
run_course_case('coordinated',48);
run_course_case('primary_only',48);
run_course_case('step_check',48,5e-5);
show_results;
exportgraphics(gcf,fullfile(root,'results','control_overview.png'),'Resolution',160);
a=readtable(fullfile(root,'results','coordinated','results.csv'));
b=readtable(fullfile(root,'results','primary_only','results.csv'));
ar=a(a.time_s>=3,:);br=b(b.time_s>=3,:);
info=struct('statistics_start_s',3,'statistics_end_s',48, ...
    'primary_frequency_rmse_Hz',sqrt(mean((br.frequency_Hz-50).^2)), ...
    'coordinated_frequency_rmse_Hz',sqrt(mean((ar.frequency_Hz-50).^2)), ...
    'soc_min_pct',min(ar.SOC)*100,'soc_final_pct',a.SOC(end)*100);
fid=fopen(fullfile(root,'results','demo_metrics.json'),'w');
fprintf(fid,'%s',jsonencode(info,PrettyPrint=true));fclose(fid);
fprintf('DEMO_COMPLETED: three cases, overview figure and demo_metrics.json updated.\n');
end
