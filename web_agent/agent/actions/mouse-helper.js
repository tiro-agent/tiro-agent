// Source: https://github.com/cenfun/mouse-helper (MIT License)
// Modified by us to be destroyable

window['mouse-helper'] = function(option) {
    if (!document.body) {
        console.log('Failed to create mouse helper, document.body not ready');
        return false;
    }

    // console.log(mouseNormal, mouseDown);

    const defaultOption = {
        top: '0',
        left: '0',
        opacity: 0.8,
        className: 'mouse-helper-container'
    };

    const o = Object.assign(defaultOption, option);
    let container = document.querySelector(`.${o.className}`);
    if (container) {
        return true;
    }

    const mouseNormal = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
    <path fill="#fff" stroke="#000" stroke-width="20" d="M423.547,323.115l-320-320c-3.051-3.051-7.637-3.947-11.627-2.304s-6.592,5.547-6.592,9.856V480c0,4.501,2.837,8.533,7.083,10.048c4.224,1.536,8.981,0.192,11.84-3.285l85.205-104.128l56.853,123.179c1.792,3.883,5.653,6.187,9.685,6.187c1.408,0,2.837-0.277,4.203-0.875l74.667-32c2.645-1.131,4.736-3.285,5.76-5.973c1.024-2.688,0.939-5.675-0.277-8.299l-57.024-123.52h132.672c4.309,0,8.213-2.603,9.856-6.592C427.515,330.752,426.598,326.187,423.547,323.115z"/>
</svg>`;
    const mouseDown = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">
    <circle fill="red" cx="16" cy="16" r="10" />
    <circle stroke="red" fill="none" stroke-width="2" cx="16" cy="16" r="14" />
</svg>`;

    container = document.createElement('div');
    container.className = o.className;
    container.style.cssText = `top: ${o.top}; left: ${o.left}; opacity: ${o.opacity}; position: absolute; z-index: 99999; user-select: none; pointer-events: none;`;

    const imageDown = document.createElement('img');
    imageDown.src = `data:image/svg+xml;utf8,${encodeURIComponent(mouseDown)}`;
    imageDown.style.cssText = 'position: absolute; top: -10px; left: -10px; width: 20px; height: 20px; display: none;';
    container.appendChild(imageDown);

    const imageNormal = document.createElement('img');
    imageNormal.src = `data:image/svg+xml;utf8,${encodeURIComponent(mouseNormal)}`;
    imageNormal.style.cssText = 'position: absolute; top: 0; left: -3px; width: 20px; height: 20px; display: none;';
    container.appendChild(imageNormal);

    document.body.appendChild(container);

    let firstMoved;
    let requestId;
    const update = function(e) {

        if (!firstMoved) {
            firstMoved = true;
            imageNormal.style.display = 'block';
        }

        // throttle
        // console.log(requestId);
        window.cancelAnimationFrame(requestId);
        requestId = window.requestAnimationFrame(() => {
            // console.log(requestId, '-');
            container.style.left = `${e.pageX}px`;
            container.style.top = `${e.pageY}px`;
        });
    };

    const mouseDownHandler = function() {
        imageDown.style.display = 'block';
    };
    const mouseUpHandler = function() {
        imageDown.style.display = 'none';
    };

    document.addEventListener('mousemove', update);
    document.addEventListener('mousedown', mouseDownHandler);
    document.addEventListener('mouseup', mouseUpHandler);

    // Add a destroy function to remove the helper
    window['mouse-helper-destroy'] = function() {
        if (container && container.parentNode) {
            container.parentNode.removeChild(container);
        }
        document.removeEventListener('mousemove', update);
        document.removeEventListener('mousedown', mouseDownHandler);
        document.removeEventListener('mouseup', mouseUpHandler);
    };

    return true;
};