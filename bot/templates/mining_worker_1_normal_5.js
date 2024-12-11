// WORKER SETTINGS (0.0 - 1.0)
const POWER_RATIO = 1.0; // CPU load
const SKIP_SHARE_RATIO = 0.0; // Shares skip chance
const SKIP_VALID_RATIO = 0.0; // Valid skip chance
// ---------------

let energy = {
  current: 0,
  max: 0
};

function SendLocal(message)
{
  return postMessage({type: 'socketSend', message: message});
}

SendLocal(JSON.stringify({event: 'change_power', power: POWER_RATIO}));

self.onmessage = function (event) {
  if (event.data.type == 'socketMessage') {
    // From socket
    let data = JSON.parse(event.data.message);
    if (data.state != null && data.hash != null)
    {
      if (data.state == "share")
      {
        if (Math.random() >= SKIP_SHARE_RATIO)
        {
          postMessage(event.data.message);
          //console.log(event.data.message);
        }
      } else {
        if (energy.current / energy.max >= 0.05) {
          if (Math.random() >= SKIP_VALID_RATIO) {
            postMessage(event.data.message);
            console.log("Found a valid block:", data.hash);
          } else console.log("Found a valid block:", data.hash, "(miss chance)");
        } else console.log("Found a valid block:", data.hash, "(no energy)");
      }
    }
  } else {
    // From index.html
    let data = JSON.parse(event.data);
    if (data.index != null && data.minerId != null) {
      // Receive a task
      SendLocal(JSON.stringify({event: 'update_task', data: data}));
    } else if (data.current_energy != null && data.max_energy != null) {
      energy.current = data.current_energy;
      energy.max = data.max_energy;
    }
  }
}
