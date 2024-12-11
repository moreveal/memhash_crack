// WS connect
let workerInstance = null;
const WS_Local = new WebSocket("ws://localhost:9100");
WS_Local.addEventListener('message', (event) => {
  workerInstance.postMessage({type: 'socketMessage', message: event.data});
});

let socketQueue = [];
WS_Local.addEventListener('open', () => {
  socketQueue.forEach(data => {
    WS_Local.send(data);
  });
  socketQueue = [];
});

function SendLocal(data)
{
  if (WS_Local.readyState === 1) {
    WS_Local.send(data);
  } else {
    socketQueue.push(data);
  }
}

// Worker hooks
const Worker_Terminate = Worker.prototype.terminate;
Worker.prototype.terminate = function() {
  SendLocal(JSON.stringify({event: 'stop_task'}));
  return Worker_Terminate.call(this);
};

const Worker_Constructor = Worker;
Worker = function(url, options)
{
  const worker = new Worker_Constructor(url, options);
  workerInstance = worker;
  
  workerInstance.addEventListener('message', (event) => {
    if (event.data.type == 'socketSend') {
      SendLocal(event.data.message);
    }
  });

  return worker;
}

// WS hooks
const WS_Send = WebSocket.prototype.send;
WebSocket.prototype.send = function (data) {
    WS_Send.call(this, data);
};

const WS_Constuctor = WebSocket;
WebSocket = function(url, protocols)
{
  if (url.indexOf('wss://memhash') != -1 && url.indexOf('token=') != -1) {
    //console.log("Memhash WS create:", url);
  }
  const wsInstance = new WS_Constuctor(url, protocols);
  if (wsInstance == null)
  {
    //console.error("Failed to connect to WebSocket");
  } else {
    
  }
  return wsInstance;
}
