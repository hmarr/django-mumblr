jQuery.fn.slugify = function(obj) {
    jQuery(this).data('obj', jQuery(obj));
    jQuery(this).keyup(function() {
        var obj = jQuery(this).data('obj');
        var slug = jQuery(this).val().replace(/\s+/g,'-').replace(/[^a-zA-Z0-9\-]/g,'').toLowerCase();
        obj.val(slug.replace(/-+/, '-'));
    });
}
$(function() {
    $('input[name=title]').slugify('input[name=slug]');
    $('#admin-box').scrollFollow({
        container: 'pagehead',
        offset: 0,
        speed: 200,
        delay: 100,
    })
});
