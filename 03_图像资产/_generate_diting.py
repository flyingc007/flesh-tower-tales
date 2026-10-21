import requests, json, pathlib
base='https://black-forest-labs-flux-1-schnell.hf.space'
prompt=("Photorealistic cinematic studio product photograph of Diting, a Chinese mythological divine beast. "
"Full body standing pose, three-quarter side view facing slightly left. Tall, slender upright wolf-like body proportions. "
"Tiger-like head, one single straight vertical horn at the exact center of the forehead, tall erect canine ears pointing upward and never drooping. "
"Long dragon-like body covered with fine dark ornamental scale patterns, qilin hooves on all four legs, powerful fluffy lion tail. "
"A balanced nine-unlike auspicious beast, natural head-neck-torso anatomy, dignified anatomy. Solemn and calm expression, deep luminous intelligent eyes, transcendent sacred presence, absolutely no cute domestic-dog feeling. "
"Pure clean seamless white studio background, hard studio lighting with frontal three-quarter key light, crisp bright rim light, high contrast, hyper-detailed fur and scale materials, realistic skin texture. "
"Commercial creature product photography, clean silhouette, complete full body inside frame, centered stable composition, ultra sharp, high detail. "
"No text, no watermark, no props, no scenery, no altar, no Buddhist statues, no clouds, no mist. "
"Avoid ugly dog, domestic pet dog, drooping ears, oversized dog head, deformed anatomy, cartoon, illustration, painterly, oil painting, halo, temple, flowers, complex background, cropped limbs, blurry low resolution.")
payload={'data':[prompt,20261020,False,1536,2048,4]}
s=requests.Session(); s.headers.update({'User-Agent':'Mozilla/5.0','Content-Type':'application/json'})
r=s.post(base+'/gradio_api/call/infer',json=payload,timeout=60); r.raise_for_status(); eid=r.json()['event_id']; print('event',eid)
result=None
with s.get(base+f'/gradio_api/call/infer/{eid}',timeout=600,stream=True) as resp:
    resp.raise_for_status()
    for line in resp.iter_lines(decode_unicode=True):
        if line and line.startswith('data:'):
            try:
                obj=json.loads(line[5:].strip())
                if isinstance(obj,list): result=obj
            except Exception: pass
if not result: raise SystemExit('no result')
img=result[0]; u=img.get('url'); u=base+u if u.startswith('/') else u
d=s.get(u,timeout=120); d.raise_for_status(); data=d.content
out=pathlib.Path('谛听_影棚定妆_02.png')
if data.startswith(b'\x89PNG'): out.write_bytes(data)
else:
    from PIL import Image
    import io
    Image.open(io.BytesIO(data)).save(out,'PNG')
print('saved',out.resolve(),out.stat().st_size)
