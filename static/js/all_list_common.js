// delete
function delete_obj(thi,obj_id){
    $.ajax({
        url: url_delete_obj,
        type: 'GET',
        data: {
            'from':thi.dataset.from,
            'obj_id':obj_id,
        },
        success:function(){
            location.reload(true);
        },
        error:function(xhr){
            console.log(xhr);
        },
    })
}
// search
let search_text=document.querySelector('.search>input[type=search]');
search_text.addEventListener('keydown',function(e){
    let keyword = search_text.value.trim();
    from = search_text.dataset.from;
    if(keyword && e.key === "Enter"){
        window.location.href = url_search+"?keyword="+keyword+"&from="+from+"&category_id="+category_id;
    }else if(keyword === "" && e.key === "Enter"){
        window.location.href = url_from
    }
})