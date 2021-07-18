# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.9.0 Dec 18 2020)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc
import wx.propgrid as pg

###########################################################################
## Class PrefsDialog
###########################################################################

class PrefsDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Preferences", pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.CAPTION|wx.RESIZE_BORDER|wx.STAY_ON_TOP )

        self.SetSizeHints( wx.Size( 400,400 ), wx.DefaultSize )

        _sizer = wx.GridBagSizer( 0, 0 )
        _sizer.SetFlexibleDirection( wx.BOTH )
        _sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self._PGM = pg.PropertyGridManager(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.propgrid.PGMAN_DEFAULT_STYLE|wx.propgrid.PG_BOLD_MODIFIED|wx.propgrid.PG_DESCRIPTION|wx.propgrid.PG_NO_INTERNAL_BORDER|wx.propgrid.PG_SPLITTER_AUTO_CENTER|wx.propgrid.PG_TOOLTIPS)
        self._PGM.SetExtraStyle( wx.propgrid.PG_EX_MODE_BUTTONS )

        self._prop_page = self._PGM.AddPage( u"Editor Preferences", wx.NullBitmap );
        _sizer.Add( self._PGM, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 1 ), wx.EXPAND, 0 )


        _sizer.Add( ( 0, 0 ), wx.GBPosition( 1, 0 ), wx.GBSpan( 1, 1 ), wx.ALL, 5 )

        _button_sizer = wx.StdDialogButtonSizer()
        self._button_sizerSave = wx.Button( self, wx.ID_SAVE )
        _button_sizer.AddButton( self._button_sizerSave )
        self._button_sizerCancel = wx.Button( self, wx.ID_CANCEL )
        _button_sizer.AddButton( self._button_sizerCancel )
        _button_sizer.Realize();

        _sizer.Add( _button_sizer, wx.GBPosition( 2, 0 ), wx.GBSpan( 1, 1 ), wx.ALIGN_CENTER_HORIZONTAL, 0 )


        _sizer.AddGrowableCol( 0 )
        _sizer.AddGrowableRow( 0 )

        self.SetSizer( _sizer )
        self.Layout()
        _sizer.Fit( self )

        self.Centre( wx.BOTH )

        # Connect Events
        self.Bind( wx.EVT_INIT_DIALOG, self.OnInitialize )
        self._PGM.Bind( pg.EVT_PG_CHANGING, self.OnEdit )
        self._button_sizerCancel.Bind( wx.EVT_BUTTON, self.OnCancel )
        self._button_sizerSave.Bind( wx.EVT_BUTTON, self.OnCommit )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnInitialize( self, event ):
        event.Skip()

    def OnEdit( self, event ):
        event.Skip()

    def OnCancel( self, event ):
        event.Skip()

    def OnCommit( self, event ):
        event.Skip()


###########################################################################
## Class bEditDialog
###########################################################################

class bEditDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Edit Cell Value", pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.CAPTION|wx.CLOSE_BOX|wx.STAY_ON_TOP )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        _sizer = wx.GridBagSizer( 0, 0 )
        _sizer.SetFlexibleDirection( wx.BOTH )
        _sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self._input = wx.TextCtrl( self, wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
        _sizer.Add( self._input, wx.GBPosition( 0, 1 ), wx.GBSpan( 1, 1 ), wx.ALIGN_CENTER_HORIZONTAL|wx.ALL|wx.EXPAND, 5 )

        self._label = wx.StaticText( self, wx.ID_ANY, u"d =", wx.DefaultPosition, wx.DefaultSize, 0 )
        self._label.Wrap( -1 )

        _sizer.Add( self._label, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 1 ), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

        _button_sizer = wx.StdDialogButtonSizer()
        self._button_sizerSave = wx.Button( self, wx.ID_SAVE )
        _button_sizer.AddButton( self._button_sizerSave )
        self._button_sizerCancel = wx.Button( self, wx.ID_CANCEL )
        _button_sizer.AddButton( self._button_sizerCancel )
        _button_sizer.Realize();

        _sizer.Add( _button_sizer, wx.GBPosition( 1, 0 ), wx.GBSpan( 1, 2 ), wx.ALL, 2 )


        self.SetSizer( _sizer )
        self.Layout()
        _sizer.Fit( self )

        self.Centre( wx.BOTH )

        # Connect Events
        self._input.Bind( wx.EVT_TEXT, self.OnText )
        self._input.Bind( wx.EVT_TEXT_ENTER, self.OnSave )
        self._button_sizerCancel.Bind( wx.EVT_BUTTON, self.OnCancel )
        self._button_sizerSave.Bind( wx.EVT_BUTTON, self.OnSave )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnText( self, event ):
        event.Skip()

    def OnSave( self, event ):
        event.Skip()

    def OnCancel( self, event ):
        event.Skip()



