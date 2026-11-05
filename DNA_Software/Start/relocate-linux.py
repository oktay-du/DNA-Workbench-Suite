"""Bind managed Linux tools to the app folder without moving scientific data."""
from pathlib import Path
import sys,json,os,re,shlex

def relocate(new,linux_base=Path('/opt/dna'),extra_files=()):
    new=Path(new).resolve()
    if not (new/'DNA_Linux/DNA-SSD/ext4.vhdx').is_file():raise ValueError('App WSL disk marker missing')
    linux_base.mkdir(parents=True,exist_ok=True);marker=linux_base/'ssd-location.json';alias=linux_base/'ssd'
    try:old=json.loads(marker.read_text())['mount']
    except (OSError,ValueError,KeyError):old='/mnt/d' # Migration of pre-portable installations only.
    if alias.exists() and not alias.is_symlink():raise ValueError('Managed app alias is a real directory; no data removed')
    temp=linux_base/'ssd.next'
    if temp.is_symlink():temp.unlink()
    temp.symlink_to(new,target_is_directory=True);os.replace(temp,alias)
    files=list((linux_base/'bin').glob('*'))+list((new/'DNA_Software/Start').glob('*'))+list(extra_files)
    files += ([Path('/etc/profile.d/dna-ssd.sh')] if linux_base==Path('/opt/dna') else [])+[linux_base/'tools/haplogrep3/haplogrep3.yaml']
    for p in files:
        if p.name=='relocate-linux.py' or p.is_symlink() or not p.is_file() or p.suffix not in ('','.sh','.py','.R','.yaml','.config'):continue
        try:text=p.read_text(encoding='utf-8-sig')
        except (OSError,UnicodeError):continue
        changed=text
        for prefix in {old,str(new)}:
            if prefix!=str(alias):changed=re.sub(re.escape(prefix)+r'(?=/|[\s\x22\x27:]|$)',lambda _:str(alias),changed)
        if changed!=text:p.write_text(changed,encoding='utf-8')
    cache=linux_base/'cache'
    for name in ('tmp','pip','xdg','huggingface','torch','npm','matplotlib','uv'):(cache/name).mkdir(parents=True,exist_ok=True)
    if hasattr(os,'geteuid') and os.geteuid()==0:
        try:
            import pwd
            user=pwd.getpwnam('dna')
            for directory in [cache,*[cache/name for name in ('tmp','pip','xdg','huggingface','torch','npm','matplotlib','uv')]]:os.chown(directory,user.pw_uid,user.pw_gid)
        except KeyError:pass
    env={'TMPDIR':str(cache/'tmp'),'TMP':str(cache/'tmp'),'TEMP':str(cache/'tmp'),'PIP_CACHE_DIR':str(cache/'pip'),'XDG_CACHE_HOME':str(cache/'xdg'),'HF_HOME':str(cache/'huggingface'),'TORCH_HOME':str(cache/'torch'),'MPLCONFIGDIR':str(cache/'matplotlib'),'UV_CACHE_DIR':str(cache/'uv'),'npm_config_cache':str(cache/'npm'),'DNA_SSD_ROOT':str(alias)}
    (linux_base/'portable-env.sh').write_text('\n'.join('export '+k+'='+shlex.quote(v) for k,v in env.items())+'\n',encoding='utf-8')
    (linux_base/'containers-need-recreate').touch();marker.write_text(json.dumps({'mount':str(new),'alias':str(alias)}),encoding='utf-8')
    return {'mount':str(new),'alias':str(alias)}

if __name__=='__main__':print(json.dumps(relocate(sys.argv[1])))
