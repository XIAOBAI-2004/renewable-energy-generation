function show_results
% Display the saved control comparison with MATLAB only; does not rerun simulation.
root=fileparts(mfilename('fullpath'));
a=readtable(fullfile(root,'results','coordinated','results.csv'));
b=readtable(fullfile(root,'results','primary_only','results.csv'));
a=a(a.time_s>=3,:);b=b(b.time_s>=3,:);
figure('Name','风光储交流微网：控制效果展示','Color','w');
tiledlayout(2,2,'TileSpacing','compact');
nexttile;plot(a.time_s,[a.P_pv_W a.P_wind_W a.P_bess_W a.P_load_W]/1e6);
title('有功协同');xlabel('时间 / s');ylabel('MW');legend('光伏','风电','储能','负荷');grid on;
nexttile;plot(b.time_s,b.frequency_Hz,'--',a.time_s,a.frequency_Hz);
yline(50,':');title('频率恢复');xlabel('时间 / s');ylabel('Hz');legend('仅一次','二次协调');grid on;
nexttile;plot(b.time_s,b.voltage_pu,'--',a.time_s,a.voltage_pu);
yline(1,':');title('母线电压');xlabel('时间 / s');ylabel('pu');legend('仅一次','二次协调');grid on;
nexttile;plot(a.time_s,100*a.SOC);
title('储能 SOC');xlabel('时间 / s');ylabel('%');grid on;
fprintf('Frequency RMSE: primary %.6f Hz -> coordinated %.6f Hz\n', ...
    sqrt(mean((b.frequency_Hz-50).^2)),sqrt(mean((a.frequency_Hz-50).^2)));
end
