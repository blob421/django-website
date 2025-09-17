
async function getSubTask(id) {
  try{ 
   const response = await fetch(`/dashboard/tasks/subtask/${id}`);
   const data = await response.json();
   return data


  } catch(error){
    console.log(error)
  }
}

function setVisibleFlex(selected , show, hide= null, hide2 = null, hide3 = null){
  
  document.getElementById(show).style.display='flex';
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


function setVisible(selected , show, hide= null, hide2 = null, hide3 = null, type=null){
  const display = type || 'block'
  document.getElementById(show).style.display=display;
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


function setVisibleDiv(show, hide= null, hide2 = null, hide3 = null){
  
  document.getElementById(show).style.display='block';
 
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

 
  function showText(){
  document.getElementById('star_comment_modal').style.display = 'block';
 
  }

function info(id){
 window.location.href=`/dashboard/projects/chart/${id}`
}

function setInfoBubble(id, id2, text=null){
       const chart_icon = document.querySelectorAll(`[id^=${id}]`);
   const info = document.getElementById(`${id2}`);
   const text_div = document.getElementById('text_value') 
   chart_icon.forEach(icon => {
      text_div.innerText= text
      const title = icon.dataset.title || text;
      icon.addEventListener('mouseenter', () => {
          const rect = icon.getBoundingClientRect();
               info.style.position = 'absolute';
               info.style.top = `${rect.bottom - 10}px`;
               info.style.left = `${rect.left + 32}px`;
    
               info.style.display='flex';
               info.innerText = title

      });
      icon.addEventListener('mouseout', () => {
         info.style.display ='none';
      });
   });
}

function setTeamBubble(){
     const chart_icon = document.querySelectorAll('[id^=people]');  
   const text_div = document.getElementById('text_team') 
   
   chart_icon.forEach(icon => {
   const info = document.getElementById('info_modal_team');

   icon.addEventListener('mouseenter', () => {
        
          const rect = icon.getBoundingClientRect();

            //Set and calculate dimensions 
            text_div.innerHTML= icon.dataset.member
            info.style.visibility = 'hidden';
            info.style.display = 'block';

            let top = rect.bottom 
            let left = rect.left + 20;
        
            const modalWidth = info.offsetWidth;
            const modalHeight = info.offsetHeight;
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;

            if (left + modalWidth > viewportWidth) {
               left = viewportWidth - modalWidth - 10;
            }

            const modalBottom = top + modalHeight;
            const maxBottom = window.innerHeight;

            if (modalBottom > maxBottom) {
            top = rect.top - modalHeight - 10; // flip above
            }
            info.style.visibility = 'visible';
          
            // Apply position
            info.style.position = 'absolute';
            info.style.top = `${top}px`;
            info.style.left = `${left}px`;
            info.style.display = 'block';
            });

      icon.addEventListener('mouseout', () => {
         info.style.display ='none';
      });
   });
}

function expandFile(id, cla){

  const div = document.getElementById(id)
  const files = document.getElementsByClassName('file_div_task_detail')
  const expanded = div.classList.contains('expanded')
  
  if (!expanded){
      div.classList.add('files_outer_div_expanded');
      div.classList.remove(cla);
      
     Array.from(files).forEach(file => {
            file.style.paddingTop = '2%'
           file.style.paddingBottom = '2%'
      })
     
  }
  else {
      div.classList.add(cla);
      div.classList.remove('files_outer_div_expanded');
      

      Array.from(files).forEach(file => {
           file.style.paddingTop = '5%'
           file.style.paddingBottom = '5%'
      })
  }
     div.classList.toggle('expanded')
}