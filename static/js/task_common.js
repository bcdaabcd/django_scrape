function editing_item_exists(){
    result = false
    saves = $('span.edit').each(function(){
        if(this.textContent === 'save') result = true;
    })
    return result;
}
function task_info_edit(thi,task_id){
    let edit_target = thi.dataset.target;
    if(thi.textContent === 'edit'){
        if(editing_item_exists() === false){
            if(thi.previousElementSibling.tagName === 'SPAN' && edit_target === 'email'){
                let obj = thi.previousElementSibling;
                let old_value = obj.textContent.trim();
                obj.outerHTML = `<input value='${old_value?old_value:""}'>`
            }else if(thi.previousElementSibling.tagName === 'SPAN' && edit_target === 'interval'){
                let obj_p = thi.previousElementSibling;
                let p_old_value = obj_p.textContent.trim();
                let obj_n = thi.previousElementSibling.previousElementSibling;
                let n_old_value = obj_n.textContent.trim();
                obj_p.outerHTML = 
                    `<select>
                        <option value="seconds">seconds</option>
                        <option value="minutes">minutes</option>
                        <option value="hours">hours</option>
                        <option value="days">days</option>
                    </select>`;
                for(let i of thi.previousElementSibling){
                    if(i.value === p_old_value) i.selected = true;
                }
                obj_n.outerHTML = `<input type='number' min=1 max='500' step=1 value='${n_old_value}' style="width:60px">`;
            }else if(thi.previousElementSibling.tagName === 'SPAN' && edit_target === 'email when'){
                let email_when = thi.previousElementSibling.previousElementSibling;
                let price_lt_old_value = thi.previousElementSibling.textContent;
                email_when.outerHTML = 
                    `<select>
                        <option value="check only">-</option>
                        <option value="every check">every check</option>
                        <option value="when price drop">when price drop</option>
                        <option value="when price lower than">when price lower than</option>
                    </select>`;
                let options = thi.previousElementSibling.previousElementSibling; // 固定当前的outerHTML
                for(let i of options){
                    if(i.value === email_when.textContent) i.selected = true;
                    if(i.value === 'when price lower than' && i.selected === true){
                        thi.previousElementSibling.outerHTML = `<input type='number' value='${price_lt_old_value}' style="width:80px">`
                    }
                }
                options.onchange = function(){
                    for(let op of options){
                        if(op.value === 'when price lower than' && op.selected === true){
                            thi.previousElementSibling.outerHTML = `<input type='number' value='${price_lt_old_value}' style="width:80px">`
                        }else{
                            thi.previousElementSibling.outerHTML = `<span></span>`
                        }
                    }
                }
            }
            thi.textContent = "save";
        }else if(editing_item_exists() === true){
            $('p.common-info').text("已存在编辑中的信息，请先保存");
        }
    }else if(thi.textContent === 'save'){
        if(thi.previousElementSibling.tagName == 'INPUT' && edit_target === 'email'){
            new_email = thi.previousElementSibling.value;
            if($(thi).parents('.task').find('span.email-when')[0].textContent != 'check only' && new_email == false){
                $('p.common-info').text("与邮件发送条件不匹配");
            }else{
                thi.previousElementSibling.outerHTML = `<span class='email-value'>${new_email?new_email:""}</span>`;
                thi.textContent = 'edit';
            }
        }else if(thi.previousElementSibling.previousElementSibling.tagName == 'INPUT' && edit_target === 'interval'){
            new_interval_n = thi.previousElementSibling.previousElementSibling.value;
            new_interval_p = thi.previousElementSibling.value;
            if(new_interval_n > 500 || new_interval_n < 1){
                $('p.common-info').text("请输入1-500的数字");
            }else{
                thi.previousElementSibling.previousElementSibling.outerHTML = `<span>${new_interval_n}</span>`;
                new_interval_p = thi.previousElementSibling.value;
                thi.previousElementSibling.outerHTML = `<span>${new_interval_p}</span>`;
                thi.textContent = 'edit';
                // console.log(`after interval: ${new_interval_n} ${new_interval_p}`);
            }
        }else if(thi.previousElementSibling.previousElementSibling.tagName === 'SELECT' && edit_target === 'email when'){
            new_price_lt = +thi.previousElementSibling.value;
            new_email_when = thi.previousElementSibling.previousElementSibling.value;
            if(new_email_when === 'when price lower than' && (new_price_lt < 0 || new_price_lt == false)){
                $('p.common-info').text('请输入正确的值');
            }else if($(thi).parents('.task').find('span.email-value')[0].textContent == false && new_email_when != 'check only'){
                $('p.common-info').text('请输入邮箱');
            }else{
                // console.log('new_price_lt: '+new_price_lt+'\n'+'new_email_when: '+new_email_when);
                thi.previousElementSibling.previousElementSibling.outerHTML = `<span class='email-when'>${new_email_when}</span>`
                thi.previousElementSibling.outerHTML = `<span>${new_price_lt?new_price_lt:""}</span>`;
                thi.textContent = 'edit';
            }
        }
        if(thi.previousElementSibling.previousElementSibling.tagName === 'SPAN' && thi.previousElementSibling.tagName === 'SPAN'){
            $('p.common-info').text("");
            $.ajax({
                url: url_task_info_edit,
                type: 'GET',
                cache: false,
                data:{
                    'task_id':task_id,
                    'target':edit_target,
                    'new_email':new_email,
                    'interval_num':new_interval_n,
                    'interval_period':new_interval_p,
                    'new_email_when':new_email_when,
                    'new_price_lt':new_price_lt,
                },
                success: function(d){
                    // console.log(d);
                },
                error: function(xhr){
                    console.log(xhr);
                }
            });
        }
    }
}
function start_or_stop_all(obj){
    let from = obj.dataset.from;
    let action = obj.dataset.action;
    $.ajax({
        url: url_start_or_stop_all,
        type: "GET",
        data:{
            'from':from,
            'action':action,
            'category_id':category_id
        },
        cache:false,
        success:function(d){
            console.log(d);
            if(d['action']==='stop'){
                for(let bu of $("div.button")){
                    if(bu.classList.contains('on')){
                        bu.classList.replace('on','stop');
                    }
                };
            }else if(d['action']==='start'){
                for(let bu of $("div.button")){
                    if(bu.classList.contains('stop')){
                        bu.classList.replace('stop','on');
                    }
                };
            }
        },
        error:function(xhr){console.log(xhr);}
    })
}
function change_task_status(obj,task_id){
    let was_on = obj.classList.contains('on');
    if(obj.classList.contains('on')){
        obj.classList.replace('on','stop');
    }else{
        obj.classList.replace('stop','on');
    }
    $.ajax({
        url: url_change_task_status,
        type: "GET",
        data: {
            'task_id' :task_id,
            'was_on' : was_on,
        },
        cache: false,
        success:function(d){
            // console.log(d);
        },
        error:function(xhr){console.log(xhr);}
    })
}