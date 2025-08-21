async function getSubTask(id) {
  try{ 
   const response = await fetch(`/dashboard/tasks/subtask/${id}`);
   const data = await response.json();
   return data


  } catch(error){
    console.log(error)
  }
}


function setVisible(selected ,show, hide= null, hide2 = null, hide3 = null){
  
  document.getElementById(show).style.display='block';
  const btn = document.querySelectorAll("button");

  btn.forEach(bt => bt.classList.remove('active'));
  selected.classList.add('active');

  if (hide3) {
      document.getElementById(hide3).style.display='none';
  }
  if (hide2) {
      document.getElementById(hide2).style.display='none';
  }
  if (hide) {
      document.getElementById(hide).style.display= 'none';
  }
 }
