// To change this, alter the code here, compress it, then replace the code
// in the add_entry.html template with the new compressed code.
javascript:(
    function() {
        var url = '{{ link_url }}';
        var args = [
            'title=' + encodeURIComponent(document.title)
        ];
        if (window.location.href.match(/youtube.com\/watch?v=/) || 
            window.location.href.match(/vimeo.com\/\d+/)) {
            url = '{{ video_url }}';
            args.push('video_url=' + encodeURIComponent(window.location.href));
        } else {
            args.push('link_url=' + encodeURIComponent(window.location.href));
        }
        window.location = url + args.join('&');
    }
)()
