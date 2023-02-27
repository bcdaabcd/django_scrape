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