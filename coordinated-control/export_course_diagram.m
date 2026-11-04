function export_course_diagram
root=fileparts(mfilename('fullpath'));m='WindPVStorage_AC_Island';
load_system(fullfile(root,[m '.slx']));
set_param(m,'PaperOrientation','landscape','PaperPositionMode','auto');
print(['-s' m],'-dpng','-r180',fullfile(root,'results','figures','00_simulink_model.png'));
close_system(m,0);
end
