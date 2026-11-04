"""Analyze actual R2025a Simulink exports and create scientific result plots."""
from pathlib import Path
import os,json
ROOT=Path(__file__).resolve().parent
os.environ['MPLBACKEND']='Agg'
cache = Path(os.environ.get('COURSE_TEMP_DIR', '/temp')) / 'renewable-energy' / 'matplotlib'
cache.mkdir(parents=True, exist_ok=True)
os.environ['MPLCONFIGDIR']=str(cache)
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
plot_font = 'DejaVu Sans'
for candidate in ['Heiti TC', 'STHeiti', 'Microsoft YaHei', 'SimHei', 'Noto Sans CJK SC', 'WenQuanYi Micro Hei']:
    try:
        fm.findfont(candidate, fallback_to_default=False)
        plot_font = candidate
        break
    except ValueError:
        pass
if plot_font == 'DejaVu Sans':
    print('Chinese font not found; install a CJK font for readable chart labels.')
plt.rcParams.update({'font.family':plot_font,
    'font.size':16,'axes.titlesize':18,'axes.labelsize':16,'legend.fontsize':14,
    'axes.spines.top':False,'axes.spines.right':False,'axes.unicode_minus':False,
    'savefig.facecolor':'white','axes.facecolor':'white','figure.facecolor':'white'})
OUT=ROOT/'results';FIG=OUT/'figures';FIG.mkdir(exist_ok=True)
cases={k:pd.read_csv(OUT/k/'results.csv') for k in ['coordinated','primary_only','step_check']}
events=[6,12,18,24,30,36,42]
event_names=['负荷增加','光照下降','风速下降','负荷切除','光照恢复','风速恢复','无功增加']
windows=[(4.5,5.5),(10.5,11.5),(16.5,17.5),(22.5,23.5),(28.5,29.5),(34.5,35.5),(40.5,41.5),(46.5,47.5)]
stages=['额定工况','负荷增加后','光照下降后','风速下降后','负荷切除后','光照恢复后','风速恢复后','无功增加后']
metrics={};rows=[]
for name,d in cases.items():
    assert np.isfinite(d.to_numpy()).all(),f'{name}: nonfinite output'
    a=d[d.time_s>=3]
    sb=np.hypot(a.P_bess_W,a.Q_bess_var)
    m={'samples':len(d),'all_finite':True,'statistics_start_s':3,
       'f_min_Hz':float(a.frequency_Hz.min()),'f_max_Hz':float(a.frequency_Hz.max()),
       'f_rmse_Hz':float(np.sqrt(np.mean((a.frequency_Hz-50)**2))),
       'u_min_pu':float(a.voltage_pu.min()),'u_max_pu':float(a.voltage_pu.max()),
       'u_rmse_pu':float(np.sqrt(np.mean((a.voltage_pu-1)**2))),
       'pf_min':float(a.PV_PF.min()),'pf_max':float(a.PV_PF.max()),
       'bess_discharge_max_MW':float(a.P_bess_W.max()/1e6),'bess_charge_max_MW':float(-a.P_bess_W.min()/1e6),
       'bess_apparent_max_MVA':float(sb.max()/1e6),'bess_current_max_A':float(a.I_bess_rms_A.max()),
       'soc_min_pct':float(a.SOC.min()*100),'soc_final_pct':float(d.SOC.iloc[-1]*100),
       'p_balance_abs_max_W':float(a.P_balance_W.abs().max()),'q_balance_abs_max_var':float(a.Q_balance_var.abs().max()),
       'current_limiter_active':bool(a.current_limit_active.max()>0),'steady':[]}
    m['full_run_bess_abs_max_MW']=float(d.P_bess_W.abs().max()/1e6)
    m['full_run_bess_apparent_max_MVA']=float(np.hypot(d.P_bess_W,d.Q_bess_var).max()/1e6)
    m['startup_bess_abs_max_MW']=float(d.loc[d.time_s<3,'P_bess_W'].abs().max()/1e6)
    assert m['full_run_bess_abs_max_MW']<5, f'{name}: battery active rating exceeded'
    assert m['full_run_bess_apparent_max_MVA']<6, f'{name}: battery apparent rating exceeded'
    for (lo,hi),stage in zip(windows,stages):
        b=d[(d.time_s>=lo)&(d.time_s<=hi)].mean()
        row={'case':name,'stage':stage,'start_s':lo,'end_s':hi,
            **{k:float(b[k]) for k in ['P_pv_W','Q_pv_var','P_wind_W','P_bess_W','Q_bess_var','P_load_W','Q_load_var','frequency_Hz','voltage_pu','PV_PF','SOC']}}
        rows.append(row);m['steady'].append(row)
    m['steady_f_abs_max_Hz']=max(abs(r['frequency_Hz']-50) for r in m['steady'])
    m['steady_u_abs_max_pct']=max(abs(r['voltage_pu']-1)*100 for r in m['steady'])
    m['frequency_settling_0p01Hz_s']=[]
    for e in events:
        b=d[(d.time_s>=e)&(d.time_s<e+6)]
        outside=b.loc[(b.frequency_Hz-50).abs()>.01,'time_s']
        last=float(outside.max()) if len(outside) else e
        m['frequency_settling_0p01Hz_s'].append(None if last>e+5.98 else round(max(0,last-e+.001),3))
    metrics[name]=m
pd.DataFrame(rows).to_csv(OUT/'steady-state-summary.csv',index=False,encoding='utf-8-sig')
a=cases['coordinated'];b=cases['step_check'];sel=a.time_s>=3
step={}
for col in ['frequency_Hz','voltage_pu','P_pv_W','P_wind_W','P_bess_W','PV_PF']:
    dif=a.loc[sel,col].to_numpy()-np.interp(a.loc[sel,'time_s'],b.time_s,b[col])
    step[col]={'rmse':float(np.sqrt(np.mean(dif**2))),'max_abs':float(abs(dif).max())}
metrics['step_comparison']=step
metrics['frequency_rmse_reduction_pct']=100*(1-metrics['coordinated']['f_rmse_Hz']/metrics['primary_only']['f_rmse_Hz'])
metrics['steady_voltage_error_reduction_pct']=100*(1-metrics['coordinated']['steady_u_abs_max_pct']/metrics['primary_only']['steady_u_abs_max_pct'])
(OUT/'metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2))

C={'pv':'#C28616','wind':'#21816D','bess':'#2166AC','load':'#343A40','primary':'#BF6845','coord':'#2166AC'}
def axis(ax,ylabel,ev=True):
    ax.set(xlim=(3,48),xlabel='时间 / s',ylabel=ylabel);ax.grid(axis='y',color='#D5DADF',alpha=.65)
    if ev:
        for e in events:ax.axvline(e,color='#B4BCC4',ls=':',lw=.7,zorder=0)
def save(fig,name):
    fig.savefig(FIG/name,dpi=180,bbox_inches='tight');plt.close(fig)
def line(ax,d,col,label,color,scale=1,ls='-'):
    ds=d[d.time_s>=3].iloc[::5]
    ax.plot(ds.time_s,ds[col]/scale,label=label,color=color,lw=1.7,ls=ls)
d=cases['coordinated'];base=cases['primary_only']

fig,axs=plt.subplots(2,1,figsize=(11.5,4.3),layout='constrained',sharex=True,gridspec_kw={'height_ratios':[1.4,1]})
line(axs[0],d,'P_pv_W','光伏有功 / MW',C['pv'],1e6);line(axs[0],d,'Q_pv_var','光伏无功 / MVAr',C['bess'],1e6)
axis(axs[0],'MW / MVAr');axs[0].legend(ncol=2,loc='upper right');axs[0].set_ylim(0,6)
line(axs[1],d,'PV_PF','光伏接入点功率因数',C['bess']);axs[1].axhline(.9,color='#555555',ls='--',lw=1,label='目标 0.9')
axis(axs[1],'功率因数');axs[1].set_ylim(.89,.91);axs[1].legend(ncol=2,loc='upper right')
save(fig,'01_pv_power_factor.png')

fig,ax=plt.subplots(figsize=(11.5,4.5),layout='constrained')
for col,label,c in [('P_load_W','负荷',C['load']),('P_pv_W','光伏',C['pv']),('P_wind_W','风电',C['wind']),('P_bess_W','储能（正：放电；负：充电）',C['bess'])]:line(ax,d,col,label,c,1e6)
axis(ax,'有功功率 / MW');ax.axhline(0,color='#555555',lw=.8);ax.set_ylim(-3,14.2);ax.legend(ncol=4,loc='upper center',bbox_to_anchor=(.5,1.13))
for e,n in zip(events,event_names):ax.text(e+.25,13.5,n,fontsize=11,color='#666666',rotation=0,ha='left')
save(fig,'02_multi_source_active_power.png')

fig,ax=plt.subplots(figsize=(11.5,4.1),layout='constrained')
line(ax,base,'frequency_Hz','仅一次调节',C['primary'],ls='--');line(ax,d,'frequency_Hz','增加二次协调',C['coord'])
ax.axhline(50,color='#555555',lw=.8);axis(ax,'母线频率 / Hz');ax.legend(ncol=2,loc='lower left');ax.set_ylim(49.56,50.17)
save(fig,'03_frequency_comparison.png')

fig,axs=plt.subplots(2,1,figsize=(11.5,4.5),layout='constrained',sharex=True)
line(axs[0],base,'voltage_pu','仅一次调节',C['primary'],ls='--');line(axs[0],d,'voltage_pu','增加二次协调',C['coord'])
axis(axs[0],'母线电压 / pu');axs[0].axhline(1,color='#777777',lw=.8);axs[0].legend(ncol=2,loc='lower left');axs[0].set_ylim(.972,1.025)
q=d.copy();q['Q_net_load']=q.Q_load_var+q.Q_filter_var
for col,label,color in [('Q_pv_var','光伏',C['pv']),('Q_bess_var','储能',C['bess']),('Q_net_load','负荷＋滤波支路',C['load'])]:line(axs[1],q,col,label,color,1e6)
axis(axs[1],'无功功率 / MVAr');axs[1].legend(ncol=3,loc='lower left');axs[1].set_ylim(-.8,4)
save(fig,'04_voltage_and_reactive_power.png')

fig,axs=plt.subplots(2,1,figsize=(11.5,4.3),layout='constrained',sharex=True)
s=d.copy();s['S_bess']=np.hypot(s.P_bess_W,s.Q_bess_var)
line(axs[0],s,'P_bess_W','有功 P / MW',C['bess'],1e6);line(axs[0],s,'S_bess','视在功率 S / MVA',C['wind'],1e6)
for val in [-5,5]:axs[0].axhline(val,color='#777777',ls='--',lw=.8)
axs[0].axhline(6,color='#A0A0A0',ls=':',lw=.8);axis(axs[0],'MW / MVA');axs[0].set_ylim(-5.6,6.7);axs[0].legend(ncol=2,loc='lower left')
line(axs[1],s,'SOC','储能 SOC（局部放大）',C['bess'],.01);axis(axs[1],'SOC / %');axs[1].set_ylim(59.79,60.01);axs[1].legend(loc='upper right')
save(fig,'05_storage_power_and_soc.png')

fig,axs=plt.subplots(2,1,figsize=(11.5,4.3),layout='constrained')
w=d[(d.time_s>=5)&(d.time_s<=5.06)].copy();ms=(w.time_s-5)*1000
for col,name,c in [('Va_V','A 相',C['bess']),('Vb_V','B 相',C['pv']),('Vc_V','C 相',C['wind'])]:axs[0].plot(ms,w[col]/1000,label=name,color=c,lw=1.7)
axs[0].set(ylabel='相电压 / kV',xlabel='相对 5 s 的时间 / ms');axs[0].legend(ncol=3,loc='upper right');axs[0].grid(axis='y',alpha=.25)
axs[1].plot(ms,w.Va_V/(11000*np.sqrt(2/3)),label='A 相电压（归一化）',color=C['bess'],lw=1.7)
axs[1].plot(ms,w.Ipv_a_A/(5e6/.9/(np.sqrt(3)*11000)*np.sqrt(2)),label='光伏 A 相电流（归一化）',color=C['pv'],lw=1.7)
axs[1].set(xlabel='相对 5 s 的时间 / ms',ylabel='归一化幅值');axs[1].legend(ncol=2,loc='upper right');axs[1].grid(axis='y',alpha=.25)
save(fig,'06_three_phase_ac_waveforms.png')

print(json.dumps({k:metrics['coordinated'][k] for k in ['f_min_Hz','f_max_Hz','f_rmse_Hz','u_min_pu','u_max_pu','bess_discharge_max_MW','bess_charge_max_MW','bess_apparent_max_MVA','soc_final_pct','steady_f_abs_max_Hz','steady_u_abs_max_pct']},ensure_ascii=False,indent=2))
print('frequency_rmse_reduction_pct',metrics['frequency_rmse_reduction_pct'])
print('step_comparison',step)
