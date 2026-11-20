export const VERT = "attribute vec2 a_position;void main(){gl_Position=vec4(a_position,0.0,1.0);}"

export const FRAG = `
#ifdef GL_FRAGMENT_PRECISION_HIGH
precision highp float;
#else
precision mediump float;
#endif
uniform vec3 u_colors[4];uniform vec2 u_res;uniform float u_time;uniform vec2 u_mouse;uniform float u_presence;
#ifdef GL_FRAGMENT_PRECISION_HIGH
#define SEED 8192.0
#else
#define SEED mod(8192.0,31.0)
#endif
vec2 hash22(vec2 p){
#ifndef GL_FRAGMENT_PRECISION_HIGH
p=mod(p,31.0);
#endif
float n=sin(dot(p,vec2(41.0,289.0)));return fract(vec2(15731.743,7892.321)*n);}
float grainHash(vec2 p){vec3 p3=fract(vec3(p.xyx)*0.1031);p3+=dot(p3,p3.yzx+33.33);return fract((p3.x+p3.y)*p3.z);}
vec3 shade(vec2 p){
vec3 color=u_colors[0]*0.35;float weight=0.35;
for(int i=0;i<4;i++){
vec2 center=(hash22(vec2(float(i),SEED))-0.5)*1.19;
float influence=exp(-dot(p-center,p-center)*9.92);
color+=u_colors[i]*influence;weight+=influence;}
return color/weight;}
void main(){
vec2 screenUv=gl_FragCoord.xy/u_res;float m=min(u_res.x,u_res.y);
vec2 p=(gl_FragCoord.xy-0.5*u_res)/m;
if(u_presence>0.001){
vec2 cursor=(0.5*u_mouse*u_res)/m;vec2 d=p-cursor;float dist=length(d);
vec2 dir=d/max(dist,0.0001);
float mask=u_presence*(1.0-smoothstep(0.0,0.569,dist));
p-=dir*mask*0.88*0.24;}
p*=1.26;p+=vec2(0.09,0.04);
p+=0.108*vec2(sin(u_time*0.31),cos(u_time*0.23));
float pe=0.002*1.26;
vec3 col=shade(p)*0.36;
col+=shade(p+vec2(pe,0.0))*0.16;col+=shade(p-vec2(pe,0.0))*0.16;
col+=shade(p+vec2(0.0,pe))*0.16;col+=shade(p-vec2(0.0,pe))*0.16;
col*=0.8;
vec2 gd=(screenUv-vec2(0.70,0.50))*vec2(u_res.x/u_res.y,1.0);
col+=vec3(0.114,0.545,1.0)*0.21*exp(-dot(gd,gd)*5.5)*(0.9+0.1*sin(u_time*0.9));
float vd=length(screenUv-0.5)*1.41421356;
col=mix(col,u_colors[0],0.75*smoothstep(0.3,1.0,vd));
col+=(grainHash(gl_FragCoord.xy+vec2(SEED*17.0,SEED*31.0))-0.5)*0.03;
gl_FragColor=vec4(clamp(col,0.0,1.0),1.0);}`