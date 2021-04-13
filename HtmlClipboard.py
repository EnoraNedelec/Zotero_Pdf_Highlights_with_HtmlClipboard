'''
Modified by RandomHardcoreJerks
    Added fix for error when clipboard busy
	Sep 24, 2013
	Requires pywin32

original: http://code.activestate.com/recipes/474121/
    # HtmlClipboard
    # An interface to the "HTML Format" clipboard data format

    __author__ = "Phillip Piper (jppx1[at]bigfoot.com)"
    __date__ = "2006-02-21"
    __version__ = "0.1"

#######################                        How to use HtmlClipboard                         ####################################
# Save this script as HtmlClipboard.py in C:\Python##\Lib\site-packages\
###
# To get clipboard with HTML:
# import HtmlClipboard
# if HtmlClipboard.HasHtml(): fragment = HtmlClipboard.GetHtml()
###
# To send HTML to the clipboard
# import HtmlClipboard
# HtmlClipboard.PutHtml("<p>It's easy!</p>")
# HtmlClipboard.PutHtml("<p>" + MyVariable + "</p>")
# for more details:	http://stackoverflow.com/questions/40439917/modifying-a-clipboard-content-to-be-treated-as-html/40789928#40789928
###
# C:\Python35\Lib\site-packages\HtmlClipboard.py


'''
# import time and import random  added by RandomHardcoreJerks to handle clipboard error when busy
import re
import time
import random
import win32clipboard

# ---------------------------------------------------------------------------
#  Convenience functions to do the most common operation


def HasHtml():
    """
    Return True if there is a Html fragment in the clipboard..
    """
    cb = HtmlClipboard()
    return cb.HasHtmlFormat()


def GetHtml():
    """
    Return the Html fragment from the clipboard or None if there is no Html in the clipboard.
    """
    cb = HtmlClipboard()
    if cb.HasHtmlFormat():
        return cb.GetFragment()
    else:
        return None


def PutHtml(fragment):
    """
    Is called in the script by: HtmlClipboard.PutHtml("<p> code example</p>")

    Put the given fragment into the clipboard.
    Convenience function to do the most common operation
    """
    cb = HtmlClipboard()
    cb.PutFragment(fragment)


# ---------------------------------------------------------------------------

class HtmlClipboard:

    CF_HTML = None

    MARKER_BLOCK_OUTPUT = \
        "Version:1.0\r\n" \
        "StartHTML:%09d\r\n" \
        "EndHTML:%09d\r\n" \
        "StartFragment:%09d\r\n" \
        "EndFragment:%09d\r\n" \
        "StartSelection:%09d\r\n" \
        "EndSelection:%09d\r\n" \
        "SourceURL:%s\r\n"
# Markerblock when there is an explicit selection
    MARKER_BLOCK_EX = \
        "Version:(\S+)\s+" \
        "StartHTML:(\d+)\s+" \
        "EndHTML:(\d+)\s+" \
        "StartFragment:(\d+)\s+" \
        "EndFragment:(\d+)\s+" \
        "StartSelection:(\d+)\s+" \
        "EndSelection:(\d+)\s+" \
        "SourceURL:(\S+)"
# re.compile = Compile a regular expression pattern into a regular expression object, which can be used in a method ei : MARKER_BLOCK_EX_RE.match(src)
    MARKER_BLOCK_EX_RE = re.compile(MARKER_BLOCK_EX)

# Markerblock when there is NO explicit selection
    MARKER_BLOCK = \
        "Version:(\S+)\s+" \
        "StartHTML:(\d+)\s+" \
        "EndHTML:(\d+)\s+" \
        "StartFragment:(\d+)\s+" \
        "EndFragment:(\d+)\s+" \
        "SourceURL:(\S+)"
    MARKER_BLOCK_RE = re.compile(MARKER_BLOCK)

    DEFAULT_HTML_BODY = \
        "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0 Transitional//EN\">" \
        "<HTML><HEAD></HEAD><BODY><!--StartFragment-->%s<!--EndFragment--></BODY></HTML>"

    def __init__(self):
        self.html = None
        self.fragment = None
        self.selection = None
        self.source = None
        self.htmlClipboardVersion = None

    def GetCfHtml(self):
        """
        Return the FORMATID of the HTML format
        """
        if self.CF_HTML is None:
            self.CF_HTML = win32clipboard.RegisterClipboardFormat(
                "HTML Format")

        return self.CF_HTML

    def GetAvailableFormats(self):
        """
        Return a possibly empty list of formats available on the clipboard
        """
        formats = []
        try:
            win32clipboard.OpenClipboard(0)
            cf = win32clipboard.EnumClipboardFormats(0)
            while (cf != 0):
                formats.append(cf)
                cf = win32clipboard.EnumClipboardFormats(cf)
        finally:
            win32clipboard.CloseClipboard()

        return formats

    def HasHtmlFormat(self):
        """
        Return a boolean indicating if the clipboard has data in HTML format
        """
        return (self.GetCfHtml() in self.GetAvailableFormats())

    def GetFromClipboard(self):
        """
        Read and decode the HTML from the clipboard
        """

# If clipboard is used by another programs and so not accessible to the script, keep trying 5 times : implement fix from: http://teachthe.net/?p=1137

        cbOpened = False
        while not cbOpened:
            try:
                win32clipboard.OpenClipboard(0)
                src = win32clipboard.GetClipboardData(self.GetCfHtml())
                src = src.decode("UTF-8")
                # print(src)
                self.DecodeClipboardSource(src)

                cbOpened = True

                win32clipboard.CloseClipboard()
            except Exception as err:
                # If access is denied, that means that the clipboard is in use.
                # Keep trying until it's available.
                if err.winerror == 5:  # Access Denied
                    pass
                    # wait on clipboard because something else has it. we're waiting a
                    # random amount of time before we try again so we don't collide again
                    time.sleep(random.random() / 50)
                elif err.winerror == 1418:  # doesn't have board open
                    pass
                elif err.winerror == 0:  # open failure
                    pass
                else:
                    print('ERROR in Clipboard section of readcomments: %s' % err)

                    pass

 # end of handling clipboard error

    def DecodeClipboardSource(self, src):
        """
        Decode the given string to figure out the details of the HTML that's on the string
        """
        # Try the extended format first (which has an explicit selection)
        matches = self.MARKER_BLOCK_EX_RE.match(src)
        if matches:
            self.prefix = matches.group(0)
            self.htmlClipboardVersion = matches.group(1)
            self.html = src[int(matches.group(2)):int(matches.group(3))]
            self.fragment = src[int(matches.group(4)):int(matches.group(5))]
            self.selection = src[int(matches.group(6)):int(matches.group(7))]
            self.source = matches.group(8)
        else:
            # Failing that, try the version without a selection
            matches = self.MARKER_BLOCK_RE.match(src)
            if matches:
                self.prefix = matches.group(0)
                self.htmlClipboardVersion = matches.group(1)
                self.html = src[int(matches.group(2)):int(matches.group(3))]
                self.fragment = src[int(matches.group(4)):int(matches.group(5))]
                self.source = matches.group(6)
                self.selection = self.fragment

    def GetHtml(self, refresh=False):
        """
        Return the entire Html document
        """
        if not self.html or refresh:
            self.GetFromClipboard()
        return self.html

    def GetFragment(self, refresh=False):
        """
        Return the Html fragment. A fragment is well-formated HTML enclosing the selected text
        """
        if not self.fragment or refresh:
            self.GetFromClipboard()
        return self.fragment

    def GetSelection(self, refresh=False):
        """
        Return the part of the HTML that was selected. It might not be well-formed.
        """
        if not self.selection or refresh:
            self.GetFromClipboard()
        return self.selection

    def GetSource(self, refresh=False):
        """
        Return the URL of the source of this HTML
        """
        if not self.selection or refresh:
            self.GetFromClipboard()
        return self.source

    def PutFragment(self, fragment, selection=None, html=None, source=None):
        """

        Is called by def PutHtml(fragment)

        Put the given well-formed fragment of Html into the clipboard.

        selection, if given, must be a literal string within fragment.
        html, if given, must be a well-formed Html document that textually
        contains fragment and its required markers.

        fragment = My code
        html =  fragment + description and context (prefix)

        """
        if selection is None:
            selection = fragment
        if html is None:
            html = self.DEFAULT_HTML_BODY % fragment
        if source is None:
            source = "no"
        fragmentStart = html.index(fragment)
        fragmentEnd = (fragmentStart + len(fragment)) + 1000
        selectionStart = html.index(selection)
        selectionEnd = (selectionStart + len(selection)) + 1000
        self.PutToClipboard(html, fragmentStart, fragmentEnd,
                            selectionStart, selectionEnd, fragment, source)

    def PutToClipboard(self, html, fragmentStart, fragmentEnd, selectionStart, selectionEnd, fragment, source="None", ):
        """
        Replace the Clipboard contents with the given html information.
        """

        try:
            # ● 2020_10_29  error 'CloseClipboard', 'Thread does not have a clipboard open.'
            # win32clipboard.CloseClipboard()
            win32clipboard.OpenClipboard(0)
            win32clipboard.EmptyClipboard()
            src = self.EncodeClipboardSource(
                html, fragmentStart, fragmentEnd, selectionStart, selectionEnd, source)
            # print(src)
            src = src.encode("UTF-8")
            win32clipboard.SetClipboardData(self.GetCfHtml(), src)

            # add support for text mode : remove all html tag but pasre the link and add them at the end
            cleanr = re.compile(
                '<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
            rawtext = re.sub(cleanr, '', html)
            urls = re.findall(r'href=[\'"]?([^\'" >]+)', html)
            joined_urls = ', '.join(urls)
            win32clipboard.SetClipboardData(
                win32clipboard.CF_UNICODETEXT, rawtext + " " + joined_urls)
        finally:
            win32clipboard.CloseClipboard()

    def EncodeClipboardSource(self, html, fragmentStart, fragmentEnd, selectionStart, selectionEnd, source):
        """
        Join all our bits of information into a string formatted as per the HTML format specs.
        """
        # How long is the prefix going to be?
        dummyPrefix = self.MARKER_BLOCK_OUTPUT % (0, 0, 0, 0, 0, 0, source)
        lenPrefix = len(dummyPrefix)

        prefix = self.MARKER_BLOCK_OUTPUT % (lenPrefix, len(html) + lenPrefix,
                                             fragmentStart + lenPrefix, fragmentEnd + lenPrefix,
                                             selectionStart + lenPrefix, selectionEnd + lenPrefix,
                                             source)
        return (prefix + html)


def DumpHtml():

    cb = HtmlClipboard()
    print("GetAvailableFormats()=%s" % str(cb.GetAvailableFormats()))
    print("HasHtmlFormat()=%s" % str(cb.HasHtmlFormat()))
    if cb.HasHtmlFormat():
        cb.GetFromClipboard()
        print("prefix=>>>%s<<<END" % cb.prefix)
        print("htmlClipboardVersion=>>>%s<<<END" % cb.htmlClipboardVersion)
        print("GetSelection()=>>>%s<<<END" % cb.GetSelection())
        print("GetFragment()=>>>%s<<<END" % cb.GetFragment())
        print("GetHtml()=>>>%s<<<END" % cb.GetHtml())
        print("GetSource()=>>>%s<<<END" % cb.GetSource())


if __name__ == '__main__':

    def test_SimpleGetPutHtml():
        data = "<p>A simple <strong>and strong</strong> text with <a href='google.com'>a first link</a> and <a href='wikipedia.com'>a second link</a></p>"
        PutHtml(data)
        if GetHtml() == data:
            print("passed")
        else:
            print("failed")

    test_SimpleGetPutHtml()
    # DumpHtml()
