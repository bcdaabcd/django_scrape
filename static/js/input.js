let save = document.querySelector('#save');
let mail = document.querySelector('#email');
let every_check_num = document.querySelector('#interval_num');
let email_when_check = document.querySelector('#email-when-check');
let periodic_check = document.querySelector('#periodic_check');
let radios = document.querySelectorAll('input[type=radio]');
let radio = document.querySelector('#lt');
let lower_than = document.querySelector('.email input[type=number]');

// 按钮之间的关联
for(let i=0;i<radios.length;i++){
    radios[i].onclick=()=>{
        if(radio.checked){
            lower_than.required=true;
        }else{
            lower_than.required=false;
        }
        if(radios[i].checked){
            mail.required=true;
            periodic_check.checked=true;
            periodic_check.required=true;
            every_check_num.required=true;
            save.checked=true;
            save.required=true;
        }
    }
}
email_when_check.onclick=()=>{
    if(email_when_check.checked){
        periodic_check.required=true;
        every_check_num.required=true;
        mail.required=true;
        save.required=true;
        save.checked=true;
        periodic_check.checked=true;
    }else{
        every_check_num.required=false;
        periodic_check.required=false;
        mail.required=false;
        save.required=false;
    }
}
periodic_check.onclick=()=>{
    if(periodic_check.checked){
        save.checked=true;
        save.required=true;
        every_check_num.required=true;
    }else{
        every_check_num.required=false;
        save.required=false;
    }
}
