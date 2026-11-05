from pathlib import Path

base = Path(__file__).parent
for file in ["family.html", "visual.html"]:
    p = base / file
    s = p.read_text(encoding="utf-8")
    if "html.embedded header" not in s:
        s = s.replace("</style>", "html.embedded header{display:none}\n</style>")
    if "const embeddedProfile=" not in s:
        script = "const embeddedProfile=new URLSearchParams(location.hash.slice(1)).get('person')||sessionStorage.getItem('dna.profile')||'';if(window.chrome&&window.chrome.webview)document.documentElement.classList.add('embedded');\n"
        s = s.replace("<script>", "<script>\n" + script, 1)
        if file == "family.html":
            s = s.replace(
                "const s=$(id),old=s.value;",
                "const s=$(id),old=s.value||(['focus','person','ra','pa'].includes(id)?embeddedProfile:'');",
            )
            s = s.replace(
                "$('focus').onchange=()=>run(verifyCards);",
                "$('focus').onchange=()=>{sessionStorage.setItem('dna.profile',$('focus').value);run(verifyCards)};",
            )
        else:
            s = s.replace(
                "const old=$('person').value;",
                "const old=$('person').value||embeddedProfile;",
            )
            s = s.replace(
                "$('person').onchange=choosePerson;",
                "$('person').onchange=()=>{sessionStorage.setItem('dna.profile',$('person').value);choosePerson()};",
            )
    p.write_text(s, encoding="utf-8")
