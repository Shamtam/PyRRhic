# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.9.0 Dec 18 2020)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class bLogPanel
###########################################################################

class bLogPanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        _sizer = wx.GridBagSizer( 0, 0 )
        _sizer.SetFlexibleDirection( wx.BOTH )
        _sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self._log_text = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.TE_LEFT|wx.TE_MULTILINE|wx.TE_READONLY|wx.TE_RICH2|wx.BORDER_NONE|wx.VSCROLL )
        self._log_text.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_WINDOW ) )

        _sizer.Add( self._log_text, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 2 ), wx.ALL|wx.EXPAND, 5 )

        _log_levelChoices = [ u"Critical", u"Error", u"Warning", u"Info", u"Debug" ]
        self._log_level = wx.RadioBox( self, wx.ID_ANY, u"Logging Level", wx.DefaultPosition, wx.DefaultSize, _log_levelChoices, 1, wx.RA_SPECIFY_ROWS )
        self._log_level.SetSelection( 4 )
        _sizer.Add( self._log_level, wx.GBPosition( 1, 0 ), wx.GBSpan( 1, 1 ), wx.ALL, 5 )

        self._log_but_clear = wx.Button( self, wx.ID_ANY, u"Clear Log", wx.DefaultPosition, wx.DefaultSize, 0 )
        _sizer.Add( self._log_but_clear, wx.GBPosition( 1, 1 ), wx.GBSpan( 1, 1 ), wx.ALIGN_CENTER, 5 )


        _sizer.AddGrowableCol( 0 )
        _sizer.AddGrowableCol( 1 )
        _sizer.AddGrowableRow( 0 )

        self.SetSizer( _sizer )
        self.Layout()

        # Connect Events
        self._log_level.Bind( wx.EVT_RADIOBOX, self.OnSetLogLevel )
        self._log_but_clear.Bind( wx.EVT_BUTTON, self.OnClearLog )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnSetLogLevel( self, event ):
        event.Skip()

    def OnClearLog( self, event ):
        event.Skip()


