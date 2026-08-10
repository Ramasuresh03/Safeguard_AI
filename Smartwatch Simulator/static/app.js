const ctx = document.getElementById('chart');
const chart = new Chart(ctx,{
  type:'line',
  data:{
    labels:[],
    datasets:[{
      label:'Heart Rate',
      data:[],
      borderWidth:2,
      tension:0.4
    }]
  }
});

function updateClock(){
  const d=new Date();
  document.getElementById("time").innerText=d.toLocaleTimeString();
  document.getElementById("date").innerText=d.toDateString();
}
setInterval(updateClock,1000);

async function updateData(){
  const r=await fetch('/data');
  const d=await r.json();

  heart.innerText=d.heart+" BPM";
  bp.innerText=d.bp;
  spo2.innerText=d.spo2+" %";
  stress.innerText=d.stress;

  chart.data.labels.push("");
  chart.data.datasets[0].data.push(d.heart);
  if(chart.data.labels.length>12){
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
  }
  chart.update();
}
setInterval(updateData,2000);

