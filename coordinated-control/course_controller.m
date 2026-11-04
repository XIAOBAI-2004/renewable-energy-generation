function [ipv,iw,eb,y] = course_controller(t,v,ip,iwm,ib,il,secondary,Ts,ic)
% Three-phase averaged converters. SI units; generation P,Q positive.
% The battery establishes voltage/frequency. PV and wind follow the AC bus.
% Parameters are engineering choices for this course, not manufacturer data.
%#codegen
persistent fp theta ep soc pp pw pref xi uv pfilt qfilt ufilt fm oldangle pc qc wc pll pllint wqc
if isempty(fp)
    fp=50; theta=0; ep=1; soc=.60; pp=5e6; pw=5e6;
    pref=0; xi=0; uv=0; pfilt=0; qfilt=0; ufilt=1;
    fm=50; oldangle=0; pc=0; qc=0; wc=0; pll=0;pllint=0;wqc=0;
end
Vpk=11000*sqrt(2/3); kq=sqrt(1/.9^2-1);
[Pp,Qp]=pq(v,ip); [Pw,Qw]=pq(v,iwm);
[Pb,Qb]=pq(v,ib); [Pl,Ql]=pq(v,il);
[Pcap,Qcap]=pq(v,ic);
va=(2*v(1)-v(2)-v(3))/3; vb=(v(2)-v(3))/sqrt(3);
vm=sqrt(va*va+vb*vb); u=vm/Vpk; ang=atan2(vb,va);
delta=atan2(sin(ang-oldangle),cos(ang-oldangle)); oldangle=ang;
if u>.4 && t>.1, fm=fm+Ts/.04*(delta/(2*pi*Ts)-fm); end
ufilt=ufilt+Ts/.02*(u-ufilt);
pfilt=pfilt+Ts/.02*(Pb-pfilt); qfilt=qfilt+Ts/.02*(Qb-qfilt);
pllerr=(-va*sin(pll)+vb*cos(pll))/max(Vpk*ufilt,.2*Vpk);
pllint=lim(pllint+Ts*4000*pllerr,-20*pi,20*pi);
wpll=2*pi*50+120*pllerr+pllint;

%% Irradiance and wind experiments; nameplate active power is 5 MW each.
G=1000; if t>=12 && t<30, G=700; end
wind=12; if t>=18 && t<36, wind=11.4; end
pav=min(5e6,5e6*G/1000);
wav=min(5e6,5e6*(wind/12)^3);
pp=pp+Ts/.06*(pav-pp); pw=pw+Ts/.30*(wav-pw);

%% Slow terminal-power correction compensates discrete synchronous sampling.
if t>1 && u>.8
    pc=lim(pc+Ts*5*(pp-Pp),-.15e6,.15e6);
    qc=lim(qc+Ts*8*(kq*Pp-Qp),-.3e6,.3e6);
    wc=lim(wc+Ts*5*(pw-Pw),-.15e6,.15e6);
    wqc=lim(wqc-Ts*8*Qw,-.3e6,.3e6);
end
pcommand=max(0,pp+pc); qcommand=kq*pp+qc;
scale=min(1,6e6/max(sqrt(pcommand^2+qcommand^2),1));
pcommand=pcommand*scale; qcommand=qcommand*scale;
phase=pll+wpll*Ts; ph=[phase;phase-2*pi/3;phase+2*pi/3];
pll=mod(pll+wpll*Ts,2*pi);
den=max(ufilt,.8)*Vpk; lowvoltage=min(max(ufilt/.8,0),1)*min(t/.25,1)^2;
ipv=2/(3*den)*(pcommand*cos(ph)+qcommand*sin(ph))*lowvoltage;
iw=2/(3*den)*(max(0,pw+wc)*cos(ph)+wqc*sin(ph))*lowvoltage;
% Two percent current margin covers the small startup voltage overshoot.
ipv=ipv*min(1,(.98*6e6/(sqrt(3)*11000))/max(norm(ipv)/sqrt(3),1));
iw=iw*min(1,(5.5e6/(sqrt(3)*11000))/max(norm(iw)/sqrt(3),1));

%% Secondary coordination: measured residual demand feedforward plus f/V PI.
if secondary>.5 && t>1
    xi=lim(xi+Ts*1e6*(50-fm),-1e6,1e6);
    ptarget=lim(Pl-Pp-Pw+xi,-5e6,5e6);
    pref=pref+Ts/.15*(ptarget-pref);
    uv=lim(uv+Ts*.8*(1-ufilt),-.15,.15);
else
    pref=0; xi=0; uv=0;
end
% VSG swing equation, H=2 s, Sbase=6 MVA; 0.5 Hz/5 MW primary droop.
fp=fp+Ts*50/(2*2*6e6)*(pref-pfilt-10e6*(fp-50));
etarget=lim(1+uv-.02*qfilt/1e6,.85,1.15);
ep=ep+Ts/.05*(etarget-ep);
phb=[theta;theta-2*pi/3;theta+2*pi/3];
ib_rms=norm(ib)/sqrt(3); Imax=6e6/(sqrt(3)*11000);
% Extra virtual resistance only above 1.15 pu current; not active in tests.
rv=lim((ib_rms/Imax-1.15)*10,0,3);
eb=Vpk*ep*min(t/.25,1)*cos(phb)-rv*ib;
theta=mod(theta+2*pi*fp*Ts,2*pi);
% Battery energy includes series-resistance losses and 96% efficiency.
pdc=Pb+3*.15*ib_rms^2;
if pdc>=0, de=pdc/.96; else, de=pdc*.96; end
soc=soc-Ts*de/(10e6*3600);
PF=abs(Pp)/max(sqrt(Pp^2+Qp^2),1);
y=[Pp;Qp;Pw;Qw;Pb;Qb;Pl;Ql;fm;u;fp;soc;PF;pref;ep;G;wind;pav;wav;ib_rms;norm(ip)/sqrt(3);norm(iwm)/sqrt(3);Pp+Pw+Pb-Pl-Pcap;Qp+Qw+Qb-Ql-Qcap;pdc;double(rv>0);v;ip;ib;Pcap;Qcap];
end

function [P,Q]=pq(v,i)
va=(2*v(1)-v(2)-v(3))/3; vb=(v(2)-v(3))/sqrt(3);
ia=(2*i(1)-i(2)-i(3))/3; ib=(i(2)-i(3))/sqrt(3);
P=dot(v,i); Q=1.5*(vb*ia-va*ib);
end

function y=lim(x,a,b)
y=min(max(x,a),b);
end
