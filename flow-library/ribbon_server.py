from portrait_export import portrait_get, portrait_post
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
import json,sys,subprocess,math,numpy as np
from PIL import Image

import imageio_ffmpeg
root=Path(__file__).resolve().parents[1];outdir=root
src=root/'flow-library/assets/ribbon-source.png'
im=np.array(Image.open(src).convert('RGBA'));h,w=im.shape[:2];c=im[:,:,:3].astype(np.float32)/255;alpha=im[:,:,3]
x=(np.arange(w,dtype=np.float32)+.5)[None,:]/w;y=(np.arange(h,dtype=np.float32)+.5)[:,None]/h
across=(y-(.30+.49*np.sin(x*2.83)))*12
v=np.clip(alpha/255/.8,0,1);interior=(v*v*(3-2*v))[:,:,None]
def color(s):
 if len(s)!=7 or s[0]!='#':raise ValueError('Use a six-digit hex color')
 return np.array([int(s[i:i+2],16) for i in (1,3,5)],dtype=np.float32)
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(outdir),**kw)
 def do_GET(self):
  if not portrait_get(self):super().do_GET()
 def do_POST(self):
  if portrait_post(self):return
  if self.path!='/export':self.send_error(404);return
  try:
   settings=json.loads(self.rfile.read(int(self.headers['Content-Length'])));fmt=settings['format'];assert fmt in ['mp4','webm']
   strength=max(0,min(1.8,float(settings['strength'])));a=color(settings['color1']);b=color(settings['color2']);mode=settings['background'];assert mode in ['solid','gradient','transparent']
   bg=np.broadcast_to(a,(h,w,3)) if mode!='gradient' else np.broadcast_to(a[None,None,:]*(1-y[:,:,None])+b[None,None,:]*y[:,:,None],(h,w,3))
   dx=max(-100,min(100,float(settings.get('positionX',0))))/100*w;dy=max(-100,min(100,float(settings.get('positionY',0))))/100*h
   angle=math.radians(max(-180,min(180,float(settings.get('rotation',0)))));zoom=max(.1,min(3,float(settings.get("scale",100))/100));cs=math.cos(angle)/zoom;sn=math.sin(angle)/zoom
   affine=(cs,sn,w/2-cs*(w/2+dx)-sn*(h/2+dy),-sn,cs,h/2+sn*(w/2+dx)-cs*(h/2+dy))
   import tempfile
   with tempfile.TemporaryDirectory(dir=root/'work') as tmp:
    target=Path(tmp)/('ribbon.'+fmt)
    codec=['-c:v','libvpx-vp9','-pix_fmt','yuva420p','-auto-alt-ref','0','-b:v','0','-crf','25'] if fmt=='webm' else ['-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart']
    proc=subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(),'-v','error','-y','-f','rawvideo','-pix_fmt','rgba','-s',f'{w}x{h+1}','-r','30','-i','-','-an',*codec,str(target)],stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    for f in range(120):
     phase=f/120*np.pi*2*(-1 if settings['reverse'] else 1);travel=x*12.5663706-phase
     broad=np.sin(travel+across*.45);sheen=(.5+.5*np.sin(travel+across*.85))**8;silk=(.5+.5*np.sin(across*19+np.sin(travel)*.6))**12
     rgb=np.clip(c*(1+strength*.22*broad[:,:,None])+strength*interior*(np.array([.06,.38,.48])*sheen[:,:,None]+np.array([0,.05,.08])*(silk*sheen)[:,:,None]),0,1)*255
     aa=alpha
     if settings['mirror']:rgb=rgb[:,::-1];aa=alpha[:,::-1]
     if dx or dy or angle or zoom!=1:
      layer=np.dstack((np.uint8(rgb+.5),aa));transformed=np.array(Image.fromarray(layer,'RGBA').transform((w,h),Image.Transform.AFFINE,affine,resample=Image.Resampling.BICUBIC))
      rgb=transformed[:,:,:3].astype(np.float32);aa=transformed[:,:,3]
     if mode!='transparent' or fmt=='mp4':
      rgb=rgb*(aa[:,:,None]/255)+bg*(1-aa[:,:,None]/255);aa=np.full_like(alpha,255)
     frame=np.zeros((h+1,w,4),np.uint8);frame[:h,:,:3]=np.uint8(rgb+.5);frame[:h,:,3]=aa;frame[h]=frame[h-1]
     proc.stdin.write(frame.tobytes())
    proc.stdin.close();error=proc.stderr.read();assert proc.wait()==0,error
    data=target.read_bytes();(outdir/('ribbon-custom.'+fmt)).write_bytes(data)
   self.send_response(200);self.send_header('Content-Type','video/'+fmt);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
  except Exception as e:
   self.send_error(400,str(e))

