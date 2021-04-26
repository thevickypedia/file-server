function success() {
  if((document.getElementById("username").value==="") || (document.getElementById("password").value==="")) {
     document.getElementById('auth').disabled = true;
  } else {
     document.getElementById('auth').disabled = false;
  }
}