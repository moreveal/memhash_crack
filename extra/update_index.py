import requests
import re

link = 'https://memhash-frontend.fly.dev/index.html'
try:
    response = requests.get(link)
    if response.status_code == 200:
        html_content = response.text
    else:
        print(f"Error [Response code: {response.status_code}]")
except Exception as e:
    print(f"Error [Exception: {e}]")
    exit(1)

content = html_content

# websocket hook
content = re.sub(r'(<script src=.+?</script>)', r'\1\n\t<script src="websocket_hook.js"></script> // change me', content, 1)

# hashtag style
content = re.sub(r'\.hashtag {[^}]+}', '''.hashtag {
        font-size: 10vw;
        color: white;
        font-weight: bold;
        font-family: "Bahnschrift", "Helvetica", sans-serif;
        line-height: 1;
        opacity: 1;
        transition: opacity 0.2s ease-out;
        -webkit-backface-visibility: hidden;
        will-change: opacity;
      }
                 
'''.strip(), content)

# hashtag
content = re.sub(r'<div.+hashtag.+<\/div>', '<div class="hashtag"><p align="center">rainbow</p></div> // change me', content)

# placeholder for js
content = re.sub(r'<script src=\"main.dart.js.+?</script>', '<script async>MAIN_SCRIPT_PLACEHOLDER</script>', content)

link = 'https://memhash-frontend.fly.dev/main.dart.js?v=0.0.111'
try:
    response = requests.get(link)
    if response.status_code == 200:
        script_content = response.text
    else:
        print(f"Error [Response code: {response.status_code}]")
except Exception as e:
    print(f"Error [Exception: {e}]")
    exit(1)

content = content.replace('MAIN_SCRIPT_PLACEHOLDER', script_content, 1)

# main vars
text = '''
    // change me
    let workers = [];

    let energystate = {
        current: 0,
        max: 0
    };

    function sendEnergyToWorkers()
    {
        for (var i = 0; i < workers.length; i++) {
            workers[i].postMessage(JSON.stringify({current_energy: energystate.current, max_energy: energystate.max }));
        }
    }

    function onEnergyChange(current = null, max = null)
    {
        if (current !== null)
        {
            energystate.current = current;
        }
        if (max !== null)
        {
            energystate.max = max;
        }
        sendEnergyToWorkers();
    }
    // change me
'''
content = content.replace('function initializeDeferredHunk', text.strip() + '\nfunction initializeDeferredHunk', 1)

# energy hack
content = re.sub(r'((.)=.\..\..\(.\...\(.\..\(.,"energy"\){3}.+?(.)=..+?,"maxEnergy"\))(.+?)(return)',
                 lambda match: f"{match.group(1)}{match.group(4)}\n\t\tonEnergyChange({match.group(2)},{match.group(3)}); // change me\n{match.group(2)}=Math.floor(Math.random()*(999999-100000+1))+100000; // change me\n{match.group(5)}",
                 content, flags=re.DOTALL)

# energy decrease disable
pattern = r',\"balance\"\){3}[^+]+\..{2}(\+.)\)[^\n]+(\n)'

def comment_group(match):
    group1 = match.group(1)
    group2 = match.group(2)
  
    return match.group(0).replace(group1, f"/*{group1}*/").strip() + " // change me" + group2

content = re.sub(pattern, comment_group, content)

# ignore uint8list error:
content = re.sub(r'(.\...\(\"Error parsing Uint8List message.+?\){2})', r'// \1 // change me\n', content)

# 200 shares limit bypass:
content = re.sub(r'(if\(.>=.\..&&.\)return)', r'// \1 // change me', content)

# only one instance of worker
content = re.sub(r'((.)=0.+)(\w+)\s*=\s*(new Worker.+?\))', r'\1if(\2==0) {workers=[];} if(workers.length > 0){break;} \3 = \4; workers.push(o); // change me', content)
# send energy to workers after their create
content = re.sub(r'(workers\.push.+?})', r'\1\nsendEnergyToWorkers(); // change me\n', content, flags=re.DOTALL)

# ignore custom messages from worker for index.html
content = re.sub(r'((.)\.data,.+?if.+requestRange.+?}.+?}.+?else)', r'\1 if(typeof \2.data === "string")', content, flags=re.DOTALL)

with open('extra/index.html', 'w+', encoding='utf-8') as f:
    f.write(content)
