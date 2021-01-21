# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.9.0 Dec 18 2020)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

from wx import ScrolledWindow
import wx
import wx.xrc
import wx.dataview
import wx.grid

###########################################################################
## Class bConsolePanel
###########################################################################

class bConsolePanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
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
        _sizer.Fit( self )

        # Connect Events
        self.Bind( wx.aui.EVT_AUI_PANE_CLOSE, self.OnClosePane )
        self._log_level.Bind( wx.EVT_RADIOBOX, self.OnSetLogLevel )
        self._log_but_clear.Bind( wx.EVT_BUTTON, self.OnClearLog )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnClosePane( self, event ):
        event.Skip()

    def OnSetLogLevel( self, event ):
        event.Skip()

    def OnClearLog( self, event ):
        event.Skip()


###########################################################################
## Class bTreePanel
###########################################################################

class bTreePanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        _sizer = wx.GridBagSizer( 0, 0 )
        _sizer.SetFlexibleDirection( wx.BOTH )
        _sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self._dvc = wx.dataview.DataViewCtrl( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.dataview.DV_NO_HEADER|wx.dataview.DV_ROW_LINES )
        self._dvc.SetFont( wx.Font( 8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        _sizer.Add( self._dvc, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 1 ), wx.EXPAND, 5 )


        _sizer.AddGrowableCol( 0 )
        _sizer.AddGrowableRow( 0 )

        self.SetSizer( _sizer )
        self.Layout()
        _sizer.Fit( self )

        # Connect Events
        self.Bind( wx.aui.EVT_AUI_PANE_CLOSE, self.OnClosePane )
        self._dvc.Bind( wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnToggle, id = wx.ID_ANY )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnClosePane( self, event ):
        event.Skip()

    def OnToggle( self, event ):
        event.Skip()


###########################################################################
## Class bTablePanel
###########################################################################

class bTablePanel ( ScrolledWindow ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.ALWAYS_SHOW_SB|wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        ScrolledWindow.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        _sizer = wx.GridBagSizer( 0, 0 )
        _sizer.SetFlexibleDirection( wx.BOTH )
        _sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self._x_grid = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )

        # Grid
        self._x_grid.CreateGrid( 0, 0 )
        self._x_grid.EnableEditing( True )
        self._x_grid.EnableGridLines( True )
        self._x_grid.EnableDragGridSize( False )
        self._x_grid.SetMargins( 0, 0 )

        # Columns
        self._x_grid.AutoSizeColumns()
        self._x_grid.EnableDragColMove( False )
        self._x_grid.EnableDragColSize( False )
        self._x_grid.SetColLabelSize( 0 )
        self._x_grid.SetColLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

        # Rows
        self._x_grid.AutoSizeRows()
        self._x_grid.EnableDragRowSize( False )
        self._x_grid.SetRowLabelSize( 0 )
        self._x_grid.SetRowLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

        # Label Appearance

        # Cell Defaults
        self._x_grid.SetDefaultCellFont( wx.Font( 8, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self._x_grid.SetDefaultCellAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )
        _sizer.Add( self._x_grid, wx.GBPosition( 0, 1 ), wx.GBSpan( 1, 1 ), wx.ALIGN_BOTTOM|wx.ALIGN_LEFT|wx.LEFT, 5 )

        self._y_grid = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )

        # Grid
        self._y_grid.CreateGrid( 0, 0 )
        self._y_grid.EnableEditing( True )
        self._y_grid.EnableGridLines( True )
        self._y_grid.EnableDragGridSize( False )
        self._y_grid.SetMargins( 0, 0 )

        # Columns
        self._y_grid.AutoSizeColumns()
        self._y_grid.EnableDragColMove( False )
        self._y_grid.EnableDragColSize( False )
        self._y_grid.SetColLabelSize( 0 )
        self._y_grid.SetColLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

        # Rows
        self._y_grid.AutoSizeRows()
        self._y_grid.EnableDragRowSize( False )
        self._y_grid.SetRowLabelSize( 0 )
        self._y_grid.SetRowLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

        # Label Appearance

        # Cell Defaults
        self._y_grid.SetDefaultCellFont( wx.Font( 8, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self._y_grid.SetDefaultCellAlignment( wx.ALIGN_RIGHT, wx.ALIGN_CENTER )
        _sizer.Add( self._y_grid, wx.GBPosition( 1, 0 ), wx.GBSpan( 1, 1 ), wx.ALIGN_RIGHT|wx.ALIGN_TOP|wx.TOP, 5 )

        self._table_grid = wx.grid.Grid( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )

        # Grid
        self._table_grid.CreateGrid( 0, 0 )
        self._table_grid.EnableEditing( True )
        self._table_grid.EnableGridLines( True )
        self._table_grid.EnableDragGridSize( False )
        self._table_grid.SetMargins( 0, 0 )

        # Columns
        self._table_grid.AutoSizeColumns()
        self._table_grid.EnableDragColMove( False )
        self._table_grid.EnableDragColSize( True )
        self._table_grid.SetColLabelSize( 0 )
        self._table_grid.SetColLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

        # Rows
        self._table_grid.AutoSizeRows()
        self._table_grid.EnableDragRowSize( False )
        self._table_grid.SetRowLabelSize( 0 )
        self._table_grid.SetRowLabelAlignment( wx.ALIGN_CENTER, wx.ALIGN_CENTER )

        # Label Appearance

        # Cell Defaults
        self._table_grid.SetDefaultCellFont( wx.Font( 8, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self._table_grid.SetDefaultCellAlignment( wx.ALIGN_RIGHT, wx.ALIGN_CENTER )
        _sizer.Add( self._table_grid, wx.GBPosition( 1, 1 ), wx.GBSpan( 1, 1 ), wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.ALL, 5 )


        _sizer.AddGrowableCol( 1 )
        _sizer.AddGrowableRow( 1 )

        self.SetSizer( _sizer )
        self.Layout()
        _sizer.Fit( self )

        # Connect Events
        self.Bind( wx.aui.EVT_AUI_PANE_CLOSE, self.OnClose )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnClose( self, event ):
        event.Skip()


###########################################################################
## Class bLoggerParamPanel
###########################################################################

class bLoggerParamPanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        _sizer = wx.GridBagSizer( 0, 0 )
        _sizer.SetFlexibleDirection( wx.BOTH )
        _sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self._label_sel_pars = wx.StaticText( self, wx.ID_ANY, u"Selected Parameters", wx.DefaultPosition, wx.DefaultSize, 0 )
        self._label_sel_pars.Wrap( -1 )

        _sizer.Add( self._label_sel_pars, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 5 ), wx.ALIGN_BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 5 )

        self._selected_dvc = wx.dataview.DataViewCtrl( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.dataview.DV_MULTIPLE|wx.dataview.DV_NO_HEADER|wx.dataview.DV_ROW_LINES )
        self._selected_dvc.SetFont( wx.Font( 8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        _sizer.Add( self._selected_dvc, wx.GBPosition( 1, 0 ), wx.GBSpan( 1, 5 ), wx.EXPAND, 5 )

        self._but_add = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )

        self._but_add.SetBitmap( wx.ArtProvider.GetBitmap( wx.ART_GO_UP, wx.ART_BUTTON ) )
        self._but_add.Enable( False )

        _sizer.Add( self._but_add, wx.GBPosition( 2, 1 ), wx.GBSpan( 1, 1 ), wx.ALL, 5 )

        self._but_rem = wx.BitmapButton( self, wx.ID_ANY, wx.NullBitmap, wx.DefaultPosition, wx.DefaultSize, wx.BU_AUTODRAW|wx.BORDER_NONE )

        self._but_rem.SetBitmap( wx.ArtProvider.GetBitmap( wx.ART_GO_DOWN, wx.ART_BUTTON ) )
        self._but_rem.Enable( False )

        _sizer.Add( self._but_rem, wx.GBPosition( 2, 3 ), wx.GBSpan( 1, 1 ), wx.ALL, 5 )

        self._available_dvc = wx.dataview.DataViewCtrl( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.dataview.DV_MULTIPLE|wx.dataview.DV_NO_HEADER|wx.dataview.DV_ROW_LINES )
        self._available_dvc.SetFont( wx.Font( 8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        _sizer.Add( self._available_dvc, wx.GBPosition( 3, 0 ), wx.GBSpan( 1, 5 ), wx.EXPAND, 5 )

        self._label_av_pars = wx.StaticText( self, wx.ID_ANY, u"Available Parameters", wx.DefaultPosition, wx.DefaultSize, 0 )
        self._label_av_pars.Wrap( -1 )

        _sizer.Add( self._label_av_pars, wx.GBPosition( 4, 0 ), wx.GBSpan( 1, 5 ), wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_TOP, 5 )


        _sizer.AddGrowableCol( 0 )
        _sizer.AddGrowableCol( 2 )
        _sizer.AddGrowableCol( 4 )
        _sizer.AddGrowableRow( 1 )
        _sizer.AddGrowableRow( 3 )

        self.SetSizer( _sizer )
        self.Layout()
        _sizer.Fit( self )

        # Connect Events
        self.Bind( wx.aui.EVT_AUI_PANE_CLOSE, self.OnClosePane )
        self._selected_dvc.Bind( wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnToggle, id = wx.ID_ANY )
        self._selected_dvc.Bind( wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self.OnSelectSelected, id = wx.ID_ANY )
        self._but_add.Bind( wx.EVT_BUTTON, self.OnAddParam )
        self._but_rem.Bind( wx.EVT_BUTTON, self.OnRemoveParam )
        self._available_dvc.Bind( wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnToggle, id = wx.ID_ANY )
        self._available_dvc.Bind( wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self.OnSelectAvailable, id = wx.ID_ANY )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnClosePane( self, event ):
        event.Skip()

    def OnToggle( self, event ):
        event.Skip()

    def OnSelectSelected( self, event ):
        event.Skip()

    def OnAddParam( self, event ):
        event.Skip()

    def OnRemoveParam( self, event ):
        event.Skip()


    def OnSelectAvailable( self, event ):
        event.Skip()


###########################################################################
## Class bGaugePanel
###########################################################################

class bGaugePanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        self.SetBackgroundColour( wx.Colour( 0, 0, 0 ) )

        _sizer = wx.GridBagSizer( 0, 0 )
        _sizer.SetFlexibleDirection( wx.BOTH )
        _sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self._param_label = wx.StaticText( self, wx.ID_ANY, u"Parameter", wx.DefaultPosition, wx.DefaultSize, 0 )
        self._param_label.Wrap( -1 )

        self._param_label.SetFont( wx.Font( 12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, wx.EmptyString ) )
        self._param_label.SetForegroundColour( wx.Colour( 255, 255, 255 ) )

        _sizer.Add( self._param_label, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 2 ), wx.EXPAND|wx.LEFT|wx.TOP, 5 )

        self._value_text = wx.StaticText( self, wx.ID_ANY, u"50.0", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE )
        self._value_text.Wrap( -1 )

        self._value_text.SetFont( wx.Font( 50, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )
        self._value_text.SetForegroundColour( wx.Colour( 0, 255, 0 ) )

        _sizer.Add( self._value_text, wx.GBPosition( 2, 0 ), wx.GBSpan( 4, 2 ), wx.ALL|wx.EXPAND, 5 )

        self._max_label = wx.StaticText( self, wx.ID_ANY, u"Max:", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_LEFT )
        self._max_label.Wrap( -1 )

        self._max_label.SetForegroundColour( wx.Colour( 255, 255, 255 ) )

        _sizer.Add( self._max_label, wx.GBPosition( 0, 3 ), wx.GBSpan( 1, 1 ), 0, 5 )

        self._max_value = wx.StaticText( self, wx.ID_ANY, u"100.0", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE )
        self._max_value.Wrap( -1 )

        self._max_value.SetForegroundColour( wx.Colour( 255, 255, 255 ) )

        _sizer.Add( self._max_value, wx.GBPosition( 1, 3 ), wx.GBSpan( 1, 1 ), wx.EXPAND|wx.RIGHT, 5 )

        self._min_label = wx.StaticText( self, wx.ID_ANY, u"Min:", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_LEFT )
        self._min_label.Wrap( -1 )

        self._min_label.SetForegroundColour( wx.Colour( 255, 255, 255 ) )

        _sizer.Add( self._min_label, wx.GBPosition( 4, 3 ), wx.GBSpan( 1, 1 ), 0, 5 )

        self._min_value = wx.StaticText( self, wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, wx.ALIGN_RIGHT|wx.ST_NO_AUTORESIZE )
        self._min_value.Wrap( -1 )

        self._min_value.SetForegroundColour( wx.Colour( 255, 255, 255 ) )

        _sizer.Add( self._min_value, wx.GBPosition( 5, 3 ), wx.GBSpan( 1, 1 ), wx.BOTTOM|wx.EXPAND|wx.RIGHT, 5 )


        _sizer.AddGrowableCol( 1 )
        _sizer.AddGrowableRow( 3 )

        self.SetSizer( _sizer )
        self.Layout()
        _sizer.Fit( self )

    def __del__( self ):
        pass


###########################################################################
## Class bLoggerGaugePanel
###########################################################################

class bLoggerGaugePanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        _sizer = wx.GridSizer( 0, 2, 0, 0 )


        self.SetSizer( _sizer )
        self.Layout()
        _sizer.Fit( self )

        # Connect Events
        self.Bind( wx.aui.EVT_AUI_PANE_CLOSE, self.OnClosePane )
        self.Bind( wx.EVT_SIZE, self.OnResize )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnClosePane( self, event ):
        event.Skip()

    def OnResize( self, event ):
        event.Skip()


