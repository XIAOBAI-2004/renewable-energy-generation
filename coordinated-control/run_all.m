function run_all
% Run the saved course model; do not rebuild or overwrite user model edits.
root=fileparts(mfilename('fullpath'));
addpath(root);
run_course_case('coordinated',48);
run_course_case('primary_only',48);
run_course_case('step_check',48,5e-5);
py=getenv('COURSE_PYTHON');
if isempty(py)
    if ispc
        localPy=fullfile(root,'.venv','Scripts','python.exe');
        py='python';
    else
        localPy=fullfile(root,'.venv','bin','python');
        py='python3';
    end
    if isfile(localPy),py=localPy;end
end
cmd=sprintf('"%s" "%s"',py,fullfile(root,'analyze_course_results.py'));
[status,output]=system(cmd);fprintf('%s\n',output);
if status~=0,error('Result analysis failed. Raw simulation files are preserved.');end
fprintf('All cases and result figures completed.\n');
end
