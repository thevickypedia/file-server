let extIP = require('ext-ip')();

extIP.get().then(ip => {
    console.log(ip);
})
.catch(err => {
    console.error(err);
});