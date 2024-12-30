speech-dispatcher-viewer
========================

Speech Viewer window for `speech-dispatcher`


Installation
------------

To compile the `speech-dispatcher` module, you need the source code of speech-dispatcher
(tested with 0.11 on Debian and Ubuntu) - point `$SD_SOURCE` to the path of the source
and run `make && sudo make install`.

The viewer is written in Python3 and is a standalone file - you can copy it wherever you like,
and run it from there.


Usage
-----

Start the viewer before `speech-dispatcher` is loaded. Run them as the same user, they use a
Unix socket at `/run/user/<UID>/speech-dispatcher/viewer.sock` for communication.

Then in `speech-dispatcher`, as output module, select the `viewer` module.

In the viewer window, you can choose to forward shown speech to another speech-dispatcher module,
and enable/disable both updating the window and forwarding speech.
Note that, compared to just using the other module, this causes a delay and does not support enqueueing
and stopping speech. So prefer switching back to just speech if you don't need the viewer.

Enjoy your shown speech.
