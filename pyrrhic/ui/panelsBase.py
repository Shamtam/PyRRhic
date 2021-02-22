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
        self._log_level.Bind( wx.EVT_RADIOBOX, self.OnSetLogLevel )
        self._log_but_clear.Bind( wx.EVT_BUTTON, self.OnClearLog )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
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
        self._dvc.Bind( wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnToggle, id = wx.ID_ANY )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
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

        self._toolbar = wx.ToolBar( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TB_HORIZONTAL )
        self._t_revert = self._toolbar.AddTool( wx.ID_ANY, u"Revert", wx.ArtProvider.GetBitmap( wx.ART_MISSING_IMAGE, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Revert Changes", u"Revert Changes", None )

        self._t_inc = self._toolbar.AddTool( wx.ID_ANY, u"Increment", wx.ArtProvider.GetBitmap( wx.ART_PLUS, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Increment Selection", u"Increment Selection", None )

        self._t_dec = self._toolbar.AddTool( wx.ID_ANY, u"Decrement", wx.ArtProvider.GetBitmap( wx.ART_MINUS, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Decrement Selection", u"Decrement Selection", None )

        self._t_inc_raw = self._toolbar.AddTool( wx.ID_ANY, u"tool", wx.ArtProvider.GetBitmap( wx.ART_PLUS, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Increment Selection (Raw)", u"Increment Selection (Raw)", None )

        self._t_dec_raw = self._toolbar.AddTool( wx.ID_ANY, u"tool", wx.ArtProvider.GetBitmap( wx.ART_MINUS, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Decrement Selection (Raw)", u"Decrement Selection (Raw)", None )

        self._toolbar.AddSeparator()

        self._t_set = self._toolbar.AddTool( wx.ID_ANY, u"Set Value", wx.ArtProvider.GetBitmap( wx.ART_EDIT, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Set Value", u"Set Value", None )

        self._t_add = self._toolbar.AddTool( wx.ID_ANY, u"Add", wx.ArtProvider.GetBitmap( wx.ART_EDIT, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Add to Selection", u"Add to Selection", None )

        self._t_mult = self._toolbar.AddTool( wx.ID_ANY, u"Multiply", wx.ArtProvider.GetBitmap( wx.ART_EDIT, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Multiply Selection", u"Multiply Selection", None )

        self._toolbar.AddSeparator()

        self._t_horiz_interp = self._toolbar.AddTool( wx.ID_ANY, u"Horizontal Interpolate", wx.ArtProvider.GetBitmap( wx.ART_EDIT, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Horizontally Interpolate Selection", u"Horizontally Interpolate Selection", None )

        self._t_vert_interp = self._toolbar.AddTool( wx.ID_ANY, u"Vertical Interpolate", wx.ArtProvider.GetBitmap( wx.ART_EDIT, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Vertically Interpolate Selection", u"Vertically Interpolate Selection", None )

        self._t_2d_interp = self._toolbar.AddTool( wx.ID_ANY, u"2D Interpolate", wx.ArtProvider.GetBitmap( wx.ART_EDIT, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"2D Interpolate Selection", u"2D Interpolate Selection", None )

        self._toolbar.AddSeparator()

        self._t_pop_from_ROM = self._toolbar.AddTool( wx.ID_ANY, u"tool", wx.ArtProvider.GetBitmap( wx.ART_GOTO_FIRST, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Populate from ROM", u"Populate from loaded ROM image", None )

        self._t_pop_from_RAM = self._toolbar.AddTool( wx.ID_ANY, u"tool", wx.ArtProvider.GetBitmap( wx.ART_GO_UP, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Populate from RAM", u"Populate from connected ECU's RAM", None )

        self._t_commit = self._toolbar.AddTool( wx.ID_ANY, u"tool", wx.ArtProvider.GetBitmap( wx.ART_TICK_MARK, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_NORMAL, u"Commit changes to RAM", u"Push any changes to connected ECU's RAM", None )

        self._t_auto_commit = self._toolbar.AddTool( wx.ID_ANY, u"tool", wx.ArtProvider.GetBitmap( wx.ART_HELP_SETTINGS, wx.ART_TOOLBAR ), wx.NullBitmap, wx.ITEM_CHECK, u"Auto-commit changes", u"Automatically commit RAM changes", None )

        self._toolbar.Realize()

        _sizer.Add( self._toolbar, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 2 ), wx.EXPAND, 5 )

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
        self._table_grid.EnableDragColSize( False )
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
        _sizer.Add( self._table_grid, wx.GBPosition( 2, 1 ), wx.GBSpan( 1, 1 ), wx.ALIGN_LEFT|wx.ALIGN_TOP|wx.ALL, 5 )

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
        _sizer.Add( self._x_grid, wx.GBPosition( 1, 1 ), wx.GBSpan( 1, 1 ), wx.ALIGN_BOTTOM|wx.ALIGN_LEFT|wx.LEFT, 5 )

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
        _sizer.Add( self._y_grid, wx.GBPosition( 2, 0 ), wx.GBSpan( 1, 1 ), wx.ALIGN_RIGHT|wx.ALIGN_TOP|wx.TOP, 5 )


        _sizer.AddGrowableCol( 1 )
        _sizer.AddGrowableRow( 2 )

        self.SetSizer( _sizer )
        self.Layout()
        _sizer.Fit( self )

        # Connect Events
        self.Bind( wx.aui.EVT_AUI_PANE_CLOSE, self.OnClose )
        self.Bind( wx.EVT_TOOL, self.OnRevert, id = self._t_revert.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnIncrement, id = self._t_inc.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnDecrement, id = self._t_dec.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnIncrementRaw, id = self._t_inc_raw.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnDecrementRaw, id = self._t_dec_raw.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnSetValue, id = self._t_set.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnAddToValue, id = self._t_add.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnMultiplyValue, id = self._t_mult.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnInterpolateH, id = self._t_horiz_interp.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnInterpolateV, id = self._t_vert_interp.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnInterpolate2D, id = self._t_2d_interp.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnROMPopulate, id = self._t_pop_from_ROM.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnRAMPopulate, id = self._t_pop_from_RAM.GetId() )
        self.Bind( wx.EVT_TOOL, self.OnCommit, id = self._t_commit.GetId() )
        self._table_grid.Bind( wx.grid.EVT_GRID_CELL_CHANGED, self.OnCellChange )
        self._table_grid.Bind( wx.grid.EVT_GRID_RANGE_SELECT, self.OnSelect )
        self._table_grid.Bind( wx.grid.EVT_GRID_SELECT_CELL, self.OnSelect )
        self._table_grid.Bind( wx.EVT_KEY_DOWN, self.OnKeyDown )
        self._x_grid.Bind( wx.grid.EVT_GRID_RANGE_SELECT, self.OnSelect )
        self._x_grid.Bind( wx.grid.EVT_GRID_SELECT_CELL, self.OnSelect )
        self._x_grid.Bind( wx.EVT_KEY_DOWN, self.OnKeyDown )
        self._y_grid.Bind( wx.grid.EVT_GRID_RANGE_SELECT, self.OnSelect )
        self._y_grid.Bind( wx.grid.EVT_GRID_SELECT_CELL, self.OnSelect )
        self._y_grid.Bind( wx.EVT_KEY_DOWN, self.OnKeyDown )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnClose( self, event ):
        event.Skip()

    def OnRevert( self, event ):
        event.Skip()

    def OnIncrement( self, event ):
        event.Skip()

    def OnDecrement( self, event ):
        event.Skip()

    def OnIncrementRaw( self, event ):
        event.Skip()

    def OnDecrementRaw( self, event ):
        event.Skip()

    def OnSetValue( self, event ):
        event.Skip()

    def OnAddToValue( self, event ):
        event.Skip()

    def OnMultiplyValue( self, event ):
        event.Skip()

    def OnInterpolateH( self, event ):
        event.Skip()

    def OnInterpolateV( self, event ):
        event.Skip()

    def OnInterpolate2D( self, event ):
        event.Skip()

    def OnROMPopulate( self, event ):
        event.Skip()

    def OnRAMPopulate( self, event ):
        event.Skip()

    def OnCommit( self, event ):
        event.Skip()

    def OnCellChange( self, event ):
        event.Skip()

    def OnSelect( self, event ):
        event.Skip()


    def OnKeyDown( self, event ):
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

        self._dvc = wx.dataview.DataViewCtrl( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.dataview.DV_MULTIPLE|wx.dataview.DV_ROW_LINES )
        self._dvc.SetFont( wx.Font( 8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        _sizer.Add( self._dvc, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 1 ), wx.EXPAND, 5 )


        _sizer.AddGrowableCol( 0 )
        _sizer.AddGrowableRow( 0 )

        self.SetSizer( _sizer )
        self.Layout()
        _sizer.Fit( self )

        # Connect Events
        self.Bind( wx.aui.EVT_AUI_PANE_CLOSE, self.OnClosePane )
        self._dvc.Bind( wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnEditItem, id = wx.ID_ANY )
        self._dvc.Bind( wx.dataview.EVT_DATAVIEW_ITEM_START_EDITING, self.OnEditItem, id = wx.ID_ANY )
        self._dvc.Bind( wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self.OnUpdateParams, id = wx.ID_ANY )
        self._dvc.Bind( wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self.OnSelectParam, id = wx.ID_ANY )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnClosePane( self, event ):
        event.Skip()

    def OnEditItem( self, event ):
        event.Skip()


    def OnUpdateParams( self, event ):
        event.Skip()

    def OnSelectParam( self, event ):
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


###########################################################################
## Class bRAMTreePanel
###########################################################################

class bRAMTreePanel ( wx.Panel ):

    def __init__( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( -1,-1 ), style = wx.TAB_TRAVERSAL, name = wx.EmptyString ):
        wx.Panel.__init__ ( self, parent, id = id, pos = pos, size = size, style = style, name = name )

        _sizer = wx.GridBagSizer( 0, 0 )
        _sizer.SetFlexibleDirection( wx.BOTH )
        _sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self._gauge = wx.Gauge( self, wx.ID_ANY, 100, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL|wx.GA_VERTICAL )
        self._gauge.SetValue( 0 )
        _sizer.Add( self._gauge, wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 1 ), wx.ALL|wx.EXPAND, 5 )

        self._dvc = wx.dataview.DataViewCtrl( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.dataview.DV_NO_HEADER|wx.dataview.DV_ROW_LINES )
        self._dvc.SetFont( wx.Font( 8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        _sizer.Add( self._dvc, wx.GBPosition( 0, 1 ), wx.GBSpan( 1, 1 ), wx.EXPAND, 5 )

        self._RAM_label = wx.StaticText( self, wx.ID_ANY, u"RAM Usage: ", wx.DefaultPosition, wx.DefaultSize, 0 )
        self._RAM_label.Wrap( -1 )

        self._RAM_label.SetFont( wx.Font( 8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        _sizer.Add( self._RAM_label, wx.GBPosition( 1, 0 ), wx.GBSpan( 1, 2 ), wx.LEFT|wx.TOP, 5 )

        self._tables_label = wx.StaticText( self, wx.ID_ANY, u"Live Tables: ", wx.DefaultPosition, wx.DefaultSize, 0 )
        self._tables_label.Wrap( -1 )

        self._tables_label.SetFont( wx.Font( 8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, wx.EmptyString ) )

        _sizer.Add( self._tables_label, wx.GBPosition( 2, 0 ), wx.GBSpan( 1, 2 ), wx.BOTTOM|wx.LEFT, 5 )

        self._pull_but = wx.Button( self, wx.ID_ANY, u"Pull from ECU", wx.DefaultPosition, wx.DefaultSize, 0 )
        _sizer.Add( self._pull_but, wx.GBPosition( 3, 0 ), wx.GBSpan( 1, 2 ), wx.ALL|wx.EXPAND, 5 )

        self._push_but = wx.Button( self, wx.ID_ANY, u"Push to ECU", wx.DefaultPosition, wx.DefaultSize, 0 )
        self._push_but.Enable( False )

        _sizer.Add( self._push_but, wx.GBPosition( 4, 0 ), wx.GBSpan( 1, 2 ), wx.ALL|wx.EXPAND, 5 )


        _sizer.AddGrowableCol( 1 )
        _sizer.AddGrowableRow( 0 )

        self.SetSizer( _sizer )
        self.Layout()
        _sizer.Fit( self )

        # Connect Events
        self._dvc.Bind( wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnToggle, id = wx.ID_ANY )
        self._dvc.Bind( wx.dataview.EVT_DATAVIEW_ITEM_VALUE_CHANGED, self.OnValueChange, id = wx.ID_ANY )
        self._pull_but.Bind( wx.EVT_BUTTON, self.OnPullState )
        self._push_but.Bind( wx.EVT_BUTTON, self.OnPushState )

    def __del__( self ):
        pass


    # Virtual event handlers, overide them in your derived class
    def OnToggle( self, event ):
        event.Skip()

    def OnValueChange( self, event ):
        event.Skip()

    def OnPullState( self, event ):
        event.Skip()

    def OnPushState( self, event ):
        event.Skip()


